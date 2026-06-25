import math
import random
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from django.db.models import Q

from courses.models import TravelCourse, CourseMember, CourseDetail
from places.models import Place
from courses.serializers import TravelCourseSerializer, CourseMemberSerializer, CourseDetailSerializer
from users.models import UserPreference

User = get_user_model()

def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0  # 지구 반지름 (km)
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


class TravelCourseViewSet(viewsets.ModelViewSet):
    serializer_class = TravelCourseSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        if self.action in [
            'retrieve', 'list_members', 'spin', 'keep_place', 
            'exclude_place', 'remove_kept_place', 'swap_kept_place', 
            'swap_slot_sequence', 'generate_ai_comment', 'claim', 'save_course'
        ]:
            return TravelCourse.objects.all()
            
        if not self.request.user.is_authenticated:
            return TravelCourse.objects.filter(user__isnull=True)
            
        return TravelCourse.objects.filter(
            Q(user=self.request.user) | Q(members__user=self.request.user) | Q(user__isnull=True)
        ).distinct()

    def perform_create(self, serializer):
        if self.request.user.is_authenticated:
            course = serializer.save(user=self.request.user)
            CourseMember.objects.create(course=course, user=self.request.user, role='owner')
        else:
            course = serializer.save(user=None)
        self._generate_initial_slots(course)

    def _generate_initial_slots(self, course):
        """
        AI(Gemini + 카카오/네이버 API) 기반으로 초기 슬롯을 생성합니다.
        API 호출 실패 시 내부 DB 기반 fallback으로 자동 전환됩니다.
        """
        try:
            from recommendations.services.recommendation_service import (
                get_slot_places_for_course, pick_place_for_slot
            )
            slot_pool, parsed = get_slot_places_for_course(
                destination=course.destination,
                travel_date=str(course.start_date),
                preferences=course.preferences or f"{course.destination} 여행",
                user=self.request.user if self.request.user.is_authenticated else None,
                duration_days=course.duration_days,
                departure_time=course.departure_time.strftime('%H:%M') if course.departure_time else "09:00",
                transportation=course.transportation
            )

            used_ids = []
            
            # 처리할 특정 장소들 (카카오 검색 후 풀에 추가)
            specific_places = parsed.get('specific_places', [])
            specific_place_objs = []
            if specific_places:
                from recommendations.services.kakao_service import fetch_and_save_kakao_places
                from recommendations.services.recommendation_service import _fixed_place_to_place
                for sp_name in specific_places:
                    # 카테고리 지정 없이 지역명 + 장소명으로 카카오 텍스트 검색 (모든 업종 검색)
                    new_fps = fetch_and_save_kakao_places(course.destination, '', [sp_name])
                    if new_fps:
                        p = _fixed_place_to_place(new_fps[0], course.destination)
                        specific_place_objs.append(p)

            for day in range(1, course.duration_days + 1):
                is_last_day = (day == course.duration_days)
                is_first_day = (day == 1)
                
                if is_last_day and course.duration_days > 1:
                    day_plan = ["음식점", "관광명소", "음식점", "카페"]
                else:
                    effective_hour = course.departure_time.hour if (is_first_day and course.departure_time) else 9
                    if effective_hour < 12:
                        day_plan = ["관광명소", "음식점", "카페", "관광명소", "음식점"]
                    elif effective_hour < 17:
                        day_plan = ["음식점", "관광명소", "카페", "음식점"]
                    else:
                        day_plan = ["음식점", "관광명소"]
                    
                    if not is_last_day:
                        day_plan.append("숙박")

                for seq, category_name in enumerate(day_plan, start=1):
                    # 카테고리에 맞는 영문 키 매핑
                    jw_cat = 'spot'
                    if '음식' in category_name or '식당' in category_name or '맛집' in category_name: jw_cat = 'restaurant'
                    elif '카페' in category_name or '디저트' in category_name: jw_cat = 'cafe'
                    elif '숙소' in category_name or '호텔' in category_name or '숙박' in category_name: jw_cat = 'accommodation'
                    elif '액티비티' in category_name or '체험' in category_name: jw_cat = 'activity'

                    place = None
                    # 특정 장소가 남아있다면 우선 할당
                    if specific_place_objs:
                        place = specific_place_objs.pop(0)
                        used_ids.append(place.id)
                    else:
                        # 이미 할당된 장소들의 지역구(Gu)를 분석하여 해당 지역구 위주로 필터링
                        current_places = [c.place for c in CourseDetail.objects.filter(course=course)]
                        preferred_gu = None
                        if current_places:
                            from collections import Counter
                            gu_list = []
                            for cp in current_places:
                                parts = cp.address.split()
                                if len(parts) >= 2:
                                    gu_list.append(parts[1])
                            if gu_list:
                                preferred_gu = Counter(gu_list).most_common(1)[0][0]
                        
                        # slot_pool을 preferred_gu로 필터링한 임시 풀 생성
                        local_slot_pool = {}
                        for k, v in slot_pool.items():
                            if preferred_gu:
                                local_v = [p for p in v if preferred_gu in p.address]
                                if not local_v: # 부족하면 원본 풀 사용
                                    local_v = v
                                local_slot_pool[k] = local_v
                            else:
                                local_slot_pool[k] = v

                        last_place = None
                        if used_ids:
                            from places.models import Place
                            last_place = Place.objects.filter(id=used_ids[-1]).first()
                            
                        last_coords = (last_place.latitude, last_place.longitude) if last_place else None
                        
                        place = pick_place_for_slot(local_slot_pool, seq, used_ids, target_category=jw_cat, transportation=course.transportation, last_coords=last_coords)
                        
                        if not place and preferred_gu:
                            # 그래도 없으면 카카오 API로 해당 지역 장소 긴급 보충
                            from recommendations.services.kakao_service import fetch_and_save_kakao_places
                            from recommendations.services.recommendation_service import _fixed_place_to_place
                            jw_to_kakao = {'spot': '관광명소', 'restaurant': '음식점', 'cafe': '카페', 'activity': '액티비티', 'accommodation': '숙박'}
                            kakao_cat = jw_to_kakao.get(jw_cat, '관광명소')
                            search_region = f"{course.destination} {preferred_gu}"
                            
                            new_fps = fetch_and_save_kakao_places(search_region, kakao_cat, [])
                            if new_fps:
                                for fp in new_fps:
                                    _fixed_place_to_place(fp, search_region)
                                from places.models import Place
                                qs = Place.objects.filter(category=jw_cat, address__contains=search_region).exclude(id__in=used_ids)
                                if qs.exists():
                                    place = list(qs.order_by('?')[:1])[0]

                        if place:
                            used_ids.append(place.id)
                    
                    if place:
                        CourseDetail.objects.create(
                            course=course,
                            place=place,
                            day_number=day,
                            sequence=seq,
                            slot_name=category_name,
                            is_locked=False
                        )

            # 생성 완료 후 AI 코멘트 작성
            from recommendations.services.ai_service import generate_course_comment
            course_places = [c.place for c in CourseDetail.objects.filter(course=course)]
            if course_places:
                course.ai_comment = generate_course_comment(course.destination, course.preferences, course_places)
                course.save()

        except Exception as e:
            print(f"[AI Slot Generation] Failed: {e}. Falling back to internal DB.")
            self._generate_initial_slots_fallback(course)

    def _generate_initial_slots_fallback(self, course):
        """
        내부 DB의 Place를 랜덤으로 선택하는 기존 방식 (fallback)
        """
        veto_codes = [v.category_code for v in self.request.user.veto_categories.all()]

        dest_filter = None
        if course.destination != '랜덤':
            dest_filter = course.destination[:2]

        all_places = Place.objects.all()
        if dest_filter:
            all_places = all_places.filter(address__contains=dest_filter)

        if not all_places.exists():
            all_places = Place.objects.all()

        for day in range(1, course.duration_days + 1):
            is_last_day = (day == course.duration_days)
            # fallback에서는 일단 명소-식당-카페-식당-(숙소) 고정 패턴을 사용합니다.
            slots_count = 4 if is_last_day else 5
            
            for seq in range(1, slots_count + 1):
                if seq == 1:
                    categories = ['spot', 'activity']
                elif seq == 2:
                    categories = ['restaurant']
                elif seq == 3:
                    categories = ['cafe']
                elif seq == 4:
                    categories = ['restaurant']
                else:
                    categories = ['accommodation']

                candidates = all_places.filter(category__in=categories).exclude(category__in=veto_codes)
                
                # 중복 피하기 위해 현재 슬롯에 들어간 장소들 + 제외 목록 포함
                current_place_ids = [c.place_id for c in CourseDetail.objects.filter(course=course)]
                from courses.models import CoursePlaceExclude
                excluded_ids = [e.place_id for e in CoursePlaceExclude.objects.filter(course=course)]
                exclude_all = set(current_place_ids + excluded_ids)
                fresh_candidates = candidates.exclude(id__in=exclude_all)

                if not fresh_candidates.exists() and dest_filter:
                    # DB에 장소가 부족할 경우 카카오 API로 긴급 수집
                    from recommendations.services.kakao_service import fetch_and_save_kakao_places
                    from recommendations.services.recommendation_service import _fixed_place_to_place
                    
                    # categories의 첫 번째 요소를 기준으로 수집
                    jw_to_kakao = {'spot': '관광명소', 'restaurant': '음식점', 'cafe': '카페', 'activity': '액티비티'}
                    kakao_cat = jw_to_kakao.get(categories[0], '관광명소')
                    search_region = course.destination if course.destination != '랜덤' else dest_filter
                    
                    new_fps = fetch_and_save_kakao_places(search_region, kakao_cat, [])
                    for fp in new_fps:
                        _fixed_place_to_place(fp, search_region)
                    
                    # 다시 후보 검색
                    all_places = Place.objects.all()
                    if dest_filter:
                        all_places = all_places.filter(address__contains=dest_filter)
                    candidates = all_places.filter(category__in=categories).exclude(category__in=veto_codes)
                    fresh_candidates = candidates.exclude(id__in=exclude_all)

                if not fresh_candidates.exists():
                    # 전국 폴백
                    fresh_candidates = Place.objects.filter(category__in=categories).exclude(category__in=veto_codes).exclude(id__in=exclude_all)

                if fresh_candidates.exists():
                    # 팝업/전시회가 있으면 일반 명소보다 우선적으로 선택 (20% 확률)
                    exhibition_candidates = [p for p in fresh_candidates if '[행사/전시]' in p.name]
                    import random
                    if exhibition_candidates and random.random() < 0.2:
                        place = random.choice(exhibition_candidates)
                    else:
                        normal_candidates = [p for p in fresh_candidates if '[행사/전시]' not in p.name]
                        if not normal_candidates:
                            place = random.choice(fresh_candidates)
                        else:
                            place = random.choice(normal_candidates)
                        
                    CourseDetail.objects.create(
                        course=course,
                        place=place,
                        day_number=day,
                        sequence=seq,
                        is_locked=False
                    )

        # 생성 완료 후 AI 코멘트 작성
        from recommendations.services.ai_service import generate_course_comment
        course_places = [c.place for c in CourseDetail.objects.filter(course=course)]
        if course_places:
            course.ai_comment = generate_course_comment(course.destination, course.preferences, course_places)
            course.save()


    @action(detail=False, methods=['post'], permission_classes=[permissions.AllowAny])
    def extract_keywords(self, request):
        """
        사용자의 요구사항 텍스트에서 실시간으로 추천 해시태그용 키워드와 제목을 추출합니다.
        """
        query = request.data.get('query', '')
        from recommendations.services.ai_service import extract_realtime_keywords
        data = extract_realtime_keywords(query)
        return Response(data)

    @action(detail=True, methods=['post'])
    def save_course(self, request, pk=None):
        """
        임시저장(draft) 상태인 코스를 최종 저장(saved) 상태로 확정합니다.
        """
        course = self.get_object()
        course.status = 'saved'
        course.save()
        return Response({'status': 'Course saved successfully'})

    @action(detail=True, methods=['post'])
    def generate_ai_comment(self, request, pk=None):
        """
        현재 코스의 슬롯들을 기반으로 AI 한줄평을 다시 생성합니다.
        """
        course = self.get_object()
        from recommendations.services.ai_service import generate_course_comment
        course_places = [c.place for c in CourseDetail.objects.filter(course=course).order_by('day_number', 'sequence')]
        if course_places:
            course.ai_comment = generate_course_comment(course.destination, course.preferences, course_places)
            course.save()
        serializer = self.get_serializer(course)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def keep_place(self, request, pk=None):
        course = self.get_object()
        place_id = request.data.get('place_id')
        from courses.models import CoursePlaceKeep
        if place_id:
            CoursePlaceKeep.objects.get_or_create(course=course, place_id=place_id)
        
        # Broadcast full update
        from channels.layers import get_channel_layer
        from asgiref.sync import async_to_sync
        channel_layer = get_channel_layer()
        if channel_layer:
            async_to_sync(channel_layer.group_send)(
                f"course_{course.id}",
                {'type': 'course_update_message', 'event': 'course_changed', 'data': {}}
            )
        serializer = self.get_serializer(course)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def exclude_place(self, request, pk=None):
        course = self.get_object()
        place_id = request.data.get('place_id')
        from courses.models import CoursePlaceExclude
        if place_id:
            CoursePlaceExclude.objects.get_or_create(course=course, place_id=place_id)
            
        from channels.layers import get_channel_layer
        from asgiref.sync import async_to_sync
        channel_layer = get_channel_layer()
        if channel_layer:
            async_to_sync(channel_layer.group_send)(
                f"course_{course.id}",
                {'type': 'course_update_message', 'event': 'course_changed', 'data': {}}
            )
        serializer = self.get_serializer(course)
        return Response(serializer.data)

    @action(detail=True, methods=['delete'], url_path='remove_kept_place/(?P<place_id>[^/.]+)')
    def remove_kept_place(self, request, pk=None, place_id=None):
        course = self.get_object()
        from courses.models import CoursePlaceKeep
        CoursePlaceKeep.objects.filter(course=course, place_id=place_id).delete()
        
        from channels.layers import get_channel_layer
        from asgiref.sync import async_to_sync
        channel_layer = get_channel_layer()
        if channel_layer:
            async_to_sync(channel_layer.group_send)(
                f"course_{course.id}",
                {'type': 'course_update_message', 'event': 'course_changed', 'data': {}}
            )
        serializer = self.get_serializer(course)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def swap_kept_place(self, request, pk=None):
        course = self.get_object()
        place_id = request.data.get('place_id')
        day_number = request.data.get('day_number')
        sequence = request.data.get('sequence')
        detail = CourseDetail.objects.filter(course=course, day_number=day_number, sequence=sequence).first()
        if detail and place_id:
            detail.place_id = place_id
            detail.save()
            from courses.models import CoursePlaceKeep
            CoursePlaceKeep.objects.filter(course=course, place_id=place_id).delete()
            
        from channels.layers import get_channel_layer
        from asgiref.sync import async_to_sync
        channel_layer = get_channel_layer()
        if channel_layer:
            async_to_sync(channel_layer.group_send)(
                f"course_{course.id}",
                {'type': 'course_update_message', 'event': 'course_changed', 'data': {}}
            )
        serializer = self.get_serializer(course)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def swap_slot_sequence(self, request, pk=None):
        course = self.get_object()
        day_number = request.data.get('day_number')
        seq1 = request.data.get('seq1')
        seq2 = request.data.get('seq2')

        detail1 = CourseDetail.objects.filter(course=course, day_number=day_number, sequence=seq1).first()
        detail2 = CourseDetail.objects.filter(course=course, day_number=day_number, sequence=seq2).first()

        if detail1 and detail2:
            detail1.sequence = 9999
            detail1.save()

            detail2.sequence = seq1
            detail2.save()

            detail1.sequence = seq2
            detail1.save()

            from channels.layers import get_channel_layer
            from asgiref.sync import async_to_sync
            channel_layer = get_channel_layer()
            if channel_layer:
                async_to_sync(channel_layer.group_send)(
                    f"course_{course.id}",
                    {'type': 'course_update_message', 'event': 'course_changed', 'data': {}}
                )
        serializer = self.get_serializer(course)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def add_slot(self, request, pk=None):
        course = self.get_object()
        day_number = request.data.get('day_number')
        jw_cat = request.data.get('category')
        
        from django.db.models import Max
        max_seq = CourseDetail.objects.filter(course=course, day_number=day_number).aggregate(Max('sequence'))['sequence__max'] or 0
        new_seq = max_seq + 1
        
        jw_to_kakao = {'spot': '관광명소', 'restaurant': '음식점', 'cafe': '카페', 'activity': '액티비티', 'accommodation': '숙박'}
        category_name = jw_to_kakao.get(jw_cat, '관광명소')
        
        veto_codes = [v.category_code for v in request.user.veto_categories.all()] if (request.user and request.user.is_authenticated) else []
        candidates = Place.objects.filter(category=jw_cat).exclude(category__in=veto_codes)
        
        dest_filter = course.destination[:2] if course.destination != '랜덤' else None
        current_place_ids = [c.place_id for c in CourseDetail.objects.filter(course=course)]
        
        if dest_filter:
            candidates = candidates.filter(address__contains=dest_filter)
            
        fresh_candidates = candidates.exclude(id__in=current_place_ids)
        if not fresh_candidates.exists() and dest_filter:
            from recommendations.services.kakao_service import fetch_and_save_kakao_places
            from recommendations.services.recommendation_service import _fixed_place_to_place
            search_region = dest_filter if course.destination == '랜덤' else course.destination
            new_fps = fetch_and_save_kakao_places(search_region, category_name, [])
            for fp in new_fps:
                _fixed_place_to_place(fp, search_region)
            candidates = Place.objects.filter(category=jw_cat, address__contains=dest_filter).exclude(category__in=veto_codes)
            fresh_candidates = candidates.exclude(id__in=current_place_ids)
            
        if not fresh_candidates.exists():
            fresh_candidates = Place.objects.filter(category=jw_cat).exclude(category__in=veto_codes).exclude(id__in=current_place_ids)
            
        place = None
        if fresh_candidates.exists():
            import random
            place = list(fresh_candidates.order_by('?')[:1])[0]
            
        if place:
            detail = CourseDetail.objects.create(
                course=course,
                place=place,
                day_number=day_number,
                sequence=new_seq,
                slot_name=category_name,
                is_locked=False
            )
            from channels.layers import get_channel_layer
            from asgiref.sync import async_to_sync
            channel_layer = get_channel_layer()
            if channel_layer:
                async_to_sync(channel_layer.group_send)(
                    f"course_{course.id}",
                    {'type': 'course_update_message', 'event': 'course_changed', 'data': {}}
                )
            
        serializer = self.get_serializer(course)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def delete_slot(self, request, pk=None):
        course = self.get_object()
        day_number = request.data.get('day_number')
        sequence = request.data.get('sequence')
        
        detail = CourseDetail.objects.filter(course=course, day_number=day_number, sequence=sequence).first()
        if detail:
            detail.delete()
            remaining = CourseDetail.objects.filter(course=course, day_number=day_number).order_by('sequence')
            for idx, r in enumerate(remaining, start=1):
                if r.sequence != idx:
                    r.sequence = idx
                    r.save()
                    
            from channels.layers import get_channel_layer
            from asgiref.sync import async_to_sync
            channel_layer = get_channel_layer()
            if channel_layer:
                async_to_sync(channel_layer.group_send)(
                    f"course_{course.id}",
                    {'type': 'course_update_message', 'event': 'course_changed', 'data': {}}
                )
                
        serializer = self.get_serializer(course)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def claim(self, request, pk=None):
        course = self.get_object()
        if course.user is not None:
            return Response({"error": "이미 소유자가 있는 코스입니다."}, status=status.HTTP_400_BAD_REQUEST)
        
        course.user = request.user
        course.status = 'saved'
        course.save()
        CourseMember.objects.create(course=course, user=request.user, role='owner')
        return Response({"message": "코스가 성공적으로 저장되었습니다."})

    @action(detail=True, methods=['post'])
    def spin(self, request, pk=None):
        """
        [Re-spin 기능] 고정(Lock)되지 않은 슬롯들에 한해 동적 라우팅 알고리즘을 거쳐 장소 재추천
        """
        # get_object_or_404를 django.shortcuts에서 임포트한 함수로 바로 사용하도록 수정 (AttributeError 해결)
        course = get_object_or_404(self.get_queryset(), pk=pk)
        
        target_day = request.data.get('target_day')
        
        # 1. 전달받은 슬롯 정보 파싱 및 잠금 상태 갱신
        slots_data = request.data.get('slots', [])
        for sd in slots_data:
            day_number = sd.get('day_number')
            sequence = sd.get('sequence')
            is_locked = sd.get('is_locked', False)
            place_id = sd.get('place_id')

            detail = CourseDetail.objects.filter(course=course, day_number=day_number, sequence=sequence).first()
            if detail:
                detail.is_locked = is_locked
                if place_id:
                    detail.place_id = place_id
                detail.save()

        # 2. 고정된 슬롯들의 좌표 목록 확보
        locked_details = CourseDetail.objects.filter(course=course, is_locked=True)
        locked_coords = [(ld.place.latitude, ld.place.longitude) for ld in locked_details]

        # 3. 비토(Veto) 목록 조회
        veto_codes = [v.category_code for v in request.user.veto_categories.all()]

        # 4. 목적지 필터 설정
        primary_dest = None
        if course.destination != '랜덤':
            primary_dest = course.destination[:2]
        
        most_common_gu = None
        current_places = CourseDetail.objects.filter(course=course).exclude(place__isnull=True)
        if current_places.exists():
            from collections import Counter
            gu_list = []
            for cp in current_places:
                parts = cp.place.address.split()
                if len(parts) >= 2:
                    gu_list.append(parts[1])
            if gu_list:
                most_common_gu = Counter(gu_list).most_common(1)[0][0]

        # 5. 미잠금 슬롯 대상 재추천
        if target_day:
            unlocked_details = CourseDetail.objects.filter(course=course, is_locked=False, day_number=target_day)
        else:
            unlocked_details = CourseDetail.objects.filter(course=course, is_locked=False)
            
        for detail in unlocked_details:
            jw_cat = 'spot'
            if '음식' in detail.slot_name or '식당' in detail.slot_name or '맛집' in detail.slot_name: jw_cat = 'restaurant'
            elif '카페' in detail.slot_name or '디저트' in detail.slot_name: jw_cat = 'cafe'
            elif '숙소' in detail.slot_name or '호텔' in detail.slot_name or '숙박' in detail.slot_name: jw_cat = 'accommodation'
            elif '액티비티' in detail.slot_name or '체험' in detail.slot_name: jw_cat = 'activity'
            
            categories = [jw_cat]

            # 기본 카테고리 후보 필터링 (비토 제외)
            candidates = Place.objects.filter(category__in=categories).exclude(category__in=veto_codes)
            
            # 지역 목적지 필터 적용 (전국 대상 스핀 방지)
            if primary_dest:
                candidates = candidates.filter(address__contains=primary_dest)
            
            if most_common_gu:
                gu_candidates = candidates.filter(address__contains=most_common_gu)
                if gu_candidates.exists():
                    candidates = gu_candidates
            
            # 기존 장소 목록 수집
            current_place_ids = [c.place_id for c in CourseDetail.objects.filter(course=course)]
            from courses.models import CoursePlaceExclude
            excluded_ids = [e.place_id for e in CoursePlaceExclude.objects.filter(course=course)]
            exclude_all = set(current_place_ids + excluded_ids)
            fresh_candidates = candidates.exclude(id__in=exclude_all)
            
            if not fresh_candidates.exists() and primary_dest:
                # DB에 해당 지역 장소가 부족할 경우 카카오 API로 긴급 수집
                from recommendations.services.kakao_service import fetch_and_save_kakao_places
                from recommendations.services.recommendation_service import _fixed_place_to_place
                
                # 역방향 매핑 (spot -> 관광명소)
                jw_to_kakao = {'spot': '관광명소', 'restaurant': '음식점', 'cafe': '카페', 'activity': '액티비티', 'accommodation': '숙박'}
                kakao_cat = jw_to_kakao.get(categories[0], '관광명소')
                
                search_region = f"{primary_dest} {most_common_gu}" if (primary_dest and most_common_gu) else (primary_dest or course.destination)
                
                new_fps = fetch_and_save_kakao_places(search_region, kakao_cat, [])
                for fp in new_fps:
                    _fixed_place_to_place(fp, search_region)
                    
                # 네이버 API 긴급 수집 (전시/팝업) 추가 (categories에 spot이나 activity가 포함된 경우)
                if 'spot' in categories or 'activity' in categories:
                    from recommendations.services.naver_service import fetch_and_save_naver_events
                    from recommendations.services.recommendation_service import _temp_event_to_place
                    import datetime
                    
                    try:
                        t_date = datetime.datetime.strptime(str(course.start_date), "%Y-%m-%d").date()
                    except Exception:
                        t_date = datetime.datetime.now().date()
                        
                    naver_cat = '팝업스토어' if 'activity' in categories else '전시회'
                    new_tes = fetch_and_save_naver_events(search_region, naver_cat)
                    for te in new_tes:
                        if te.start_date <= t_date <= te.end_date:
                            _temp_event_to_place(te, search_region)
                
                # 다시 후보 검색
                candidates = Place.objects.filter(category__in=categories, address__contains=primary_dest).exclude(category__in=veto_codes)
                if most_common_gu:
                    gu_candidates = candidates.filter(address__contains=most_common_gu)
                    if gu_candidates.exists():
                        candidates = gu_candidates
                fresh_candidates = candidates.exclude(id__in=exclude_all)

            if not fresh_candidates.exists():
                # 그래도 없으면 전국 대상으로 폴백
                fresh_candidates = Place.objects.filter(category__in=categories).exclude(category__in=veto_codes).exclude(id__in=exclude_all)

            candidates = fresh_candidates

            # AI 기반 테마 매칭 및 거리 가중치 종합 계산
            pref, created = UserPreference.objects.get_or_create(user=request.user)
            user_themes = [t.strip() for t in pref.preferred_themes.split(',') if t.strip()] if pref.preferred_themes else []

            if candidates.exists():
                best_place = None
                max_score = -float('inf')

                for cand in candidates:
                    # 1. 테마 매칭 가중치 (개당 +5점)
                    cand_themes = [t.strip() for t in cand.themes.split(',') if t.strip()] if cand.themes else []
                    match_count = len(set(user_themes) & set(cand_themes))
                    theme_score = match_count * 5.0

                    # 전시회/팝업스토어는 우선순위 가중치 소폭 부여 (+2점)
                    if '[행사/전시]' in cand.name:
                        theme_score += 2.0

                    # 2. 고정 장소들과의 물리적 거리 감점 (-1.5점 per km, 대중교통은 -8.0점)
                    distance_penalty = 0.0
                    penalty_rate = 8.0 if course.transportation == 'public' else 1.5
                    
                    if locked_coords:
                        distances = [haversine(cand.latitude, cand.longitude, lat, lon) for lat, lon in locked_coords]
                        avg_dist = sum(distances) / len(distances)
                        distance_penalty = avg_dist * penalty_rate

                    # 스핀을 여러 번 할 때 매번 똑같은 장소만 추천되는 것을 방지하기 위한 랜덤 노이즈 부여 (+- 3.0점)
                    total_score = theme_score - distance_penalty + random.uniform(-3.0, 3.0)

                    if total_score > max_score:
                        max_score = total_score
                        best_place = cand

                if best_place:
                    detail.place = best_place
                    detail.save()
                    
                    # 웹소켓 브로드캐스트 추가: 다른 사람 화면에도 실시간으로 스핀 결과를 쏴줍니다.
                    try:
                        from channels.layers import get_channel_layer
                        from asgiref.sync import async_to_sync
                        channel_layer = get_channel_layer()
                        async_to_sync(channel_layer.group_send)(
                            f'course_{course.id}',
                            {
                                'type': 'course_update_message',
                                'event': 'spin_update',
                                'data': CourseDetailSerializer(detail).data
                            }
                        )
                    except Exception as e:
                        print(f"WebSocket broadcast failed: {e}")

        serializer = self.get_serializer(course)
        return Response(serializer.data, status=status.HTTP_200_OK)


class CourseMemberViewSet(viewsets.ModelViewSet):
    serializer_class = CourseMemberSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        course_id = self.kwargs.get('course_pk')
        return CourseMember.objects.filter(course_id=course_id)

    def perform_create(self, serializer):
        from rest_framework.exceptions import PermissionDenied, ValidationError

        course_id = self.kwargs.get('course_pk')
        course = get_object_or_404(TravelCourse, pk=course_id)

        # 권한 확인: 코스 소유자이거나 기존 멤버여야 초대 권한이 있음
        if not course.user == self.request.user and not CourseMember.objects.filter(course=course, user=self.request.user).exists():
            raise PermissionDenied("이 코스에 참여자를 초대할 권한이 없습니다.")

        email = self.request.data.get('email')
        if not email:
            raise ValidationError({"email": "이메일은 필수 입력 항목입니다."})

        try:
            invitee = User.objects.get(email=email)
        except User.DoesNotExist:
            raise ValidationError({"email": "해당 이메일을 가진 사용자가 존재하지 않습니다."})

        # 친구 관계 검증 (초대자와 피초대자가 친구여야 함)
        from users.models import Friendship
        from django.db.models import Q
        is_friend = Friendship.objects.filter(
            (Q(from_user=self.request.user, to_user=invitee) | Q(from_user=invitee, to_user=self.request.user))
            & Q(status='accepted')
        ).exists()

        if not is_friend:
            raise PermissionDenied("친구로 등록된 사용자만 코스에 초대할 수 있습니다.")

        # 중복 참여 체크
        if course.user == invitee or CourseMember.objects.filter(course=course, user=invitee).exists():
            raise ValidationError({"email": "이미 이 코스에 참여 중이거나 코스의 소유자입니다."})

        serializer.save(course=course, user=invitee, role='editor')
