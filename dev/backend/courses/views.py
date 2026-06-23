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
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return TravelCourse.objects.filter(
            Q(user=self.request.user) | Q(members__user=self.request.user)
        ).distinct()

    def perform_create(self, serializer):
        course = serializer.save(user=self.request.user)
        CourseMember.objects.create(course=course, user=self.request.user, role='owner')
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
            slot_pool = get_slot_places_for_course(
                destination=course.destination,
                travel_date=str(course.start_date),
                preferences=course.preferences or f"{course.destination} 여행",
                user=self.request.user
            )

            used_ids = []
            for day in range(1, course.duration_days + 1):
                for seq in range(1, 5):
                    place = pick_place_for_slot(slot_pool, seq, used_ids)
                    if place:
                        CourseDetail.objects.create(
                            course=course,
                            place=place,
                            day_number=day,
                            sequence=seq,
                            is_locked=False
                        )
                        used_ids.append(place.id)

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
            for seq in range(1, 5):
                if seq == 1:
                    categories = ['spot', 'activity']
                elif seq == 2:
                    categories = ['restaurant']
                elif seq == 3:
                    categories = ['cafe']
                else:
                    categories = ['restaurant']

                candidates = all_places.filter(category__in=categories).exclude(category__in=veto_codes)
                
                # 중복 피하기 위해 현재 슬롯에 들어간 장소들 제외
                current_place_ids = [c.place_id for c in CourseDetail.objects.filter(course=course)]
                fresh_candidates = candidates.exclude(id__in=current_place_ids)

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
                    fresh_candidates = candidates.exclude(id__in=current_place_ids)

                if not fresh_candidates.exists():
                    # 전국 폴백
                    fresh_candidates = Place.objects.filter(category__in=categories).exclude(category__in=veto_codes).exclude(id__in=current_place_ids)

                if fresh_candidates.exists():
                    # 팝업/전시회가 있으면 일반 명소보다 우선적으로 선택
                    exhibition_candidates = [p for p in fresh_candidates if '[행사/전시]' in p.name]
                    if exhibition_candidates:
                        place = random.choice(exhibition_candidates)
                    else:
                        place = random.choice(fresh_candidates)
                        
                    CourseDetail.objects.create(
                        course=course,
                        place=place,
                        day_number=day,
                        sequence=seq,
                        is_locked=False
                    )


    @action(detail=True, methods=['post'])
    def spin(self, request, pk=None):
        """
        [Re-spin 기능] 고정(Lock)되지 않은 슬롯들에 한해 동적 라우팅 알고리즘을 거쳐 장소 재추천
        """
        # get_object_or_404를 django.shortcuts에서 임포트한 함수로 바로 사용하도록 수정 (AttributeError 해결)
        course = get_object_or_404(self.get_queryset(), pk=pk)
        
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

        # 4. 목적지 필터 설정 (랜덤인 경우 고정된 장소의 지역으로 자동 고정)
        dest_filter = None
        if course.destination != '랜덤':
            dest_filter = course.destination[:2]
        else:
            # 고정된 장소가 있다면 그 위치를 기반으로 인근 지역(시/도) 필터링
            if locked_details.exists():
                first_locked_addr = locked_details.first().place.address
                if first_locked_addr:
                    dest_filter = first_locked_addr[:2] # 예: '서울', '경기', '강원'

        # 5. 미잠금 슬롯 대상 재추천
        unlocked_details = CourseDetail.objects.filter(course=course, is_locked=False)
        for detail in unlocked_details:
            if detail.sequence == 1:
                categories = ['spot', 'activity']
            elif detail.sequence == 2:
                categories = ['restaurant']
            elif detail.sequence == 3:
                categories = ['cafe']
            else:
                categories = ['restaurant']

            # 기본 카테고리 후보 필터링 (비토 제외)
            candidates = Place.objects.filter(category__in=categories).exclude(category__in=veto_codes)
            
            # 지역 목적지 필터 적용 (전국 대상 스핀 방지)
            if dest_filter:
                candidates = candidates.filter(address__contains=dest_filter)
            
            # 이미 코스 내에 할당된 장소는 중복 스킵
            current_place_ids = [c.place_id for c in CourseDetail.objects.filter(course=course)]
            fresh_candidates = candidates.exclude(id__in=current_place_ids)
            
            if not fresh_candidates.exists() and dest_filter:
                # DB에 해당 지역 장소가 부족할 경우 카카오 API로 긴급 수집
                from recommendations.services.kakao_service import fetch_and_save_kakao_places
                from recommendations.services.recommendation_service import _fixed_place_to_place
                
                # 역방향 매핑 (spot -> 관광명소)
                jw_to_kakao = {'spot': '관광명소', 'restaurant': '음식점', 'cafe': '카페', 'activity': '액티비티'}
                kakao_cat = jw_to_kakao.get(categories[0], '관광명소')
                
                # course.destination이 '랜덤'이면 dest_filter를 사용
                search_region = course.destination if course.destination != '랜덤' else dest_filter
                
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
                candidates = Place.objects.filter(category__in=categories, address__contains=dest_filter).exclude(category__in=veto_codes)
                fresh_candidates = candidates.exclude(id__in=current_place_ids)

            if not fresh_candidates.exists():
                # 그래도 없으면 전국 대상으로 폴백
                fresh_candidates = Place.objects.filter(category__in=categories).exclude(category__in=veto_codes).exclude(id__in=current_place_ids)

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

                    # 전시회/팝업스토어는 우선순위 가중치 부여 (+15점)
                    if '[행사/전시]' in cand.name:
                        theme_score += 15.0

                    # 2. 고정 장소들과의 물리적 거리 감점 (-1.5점 per km)
                    distance_penalty = 0.0
                    if locked_coords:
                        distances = [haversine(cand.latitude, cand.longitude, lat, lon) for lat, lon in locked_coords]
                        avg_dist = sum(distances) / len(distances)
                        distance_penalty = avg_dist * 1.5

                    # 스핀을 여러 번 할 때 매번 똑같은 장소만 추천되는 것을 방지하기 위한 랜덤 노이즈 부여 (+- 3.0점)
                    total_score = theme_score - distance_penalty + random.uniform(-3.0, 3.0)

                    if total_score > max_score:
                        max_score = total_score
                        best_place = cand

                if best_place:
                    detail.place = best_place

            detail.save()

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

        # 중복 참여 체크
        if course.user == invitee or CourseMember.objects.filter(course=course, user=invitee).exists():
            raise ValidationError({"email": "이미 이 코스에 참여 중이거나 코스의 소유자입니다."})

        serializer.save(course=course, user=invitee, role='editor')
