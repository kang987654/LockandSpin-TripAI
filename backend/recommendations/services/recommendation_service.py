import random
from recommendations.models import FixedPlace
from recommendations.services.ai_service import parse_user_request
from recommendations.services.kakao_service import fetch_and_save_kakao_places
from recommendations.services.naver_service import fetch_and_save_naver_events

# 카카오 카테고리 → jw Place.category 매핑
KAKAO_TO_JW_CATEGORY = {
    '카페': 'cafe',
    '음식점': 'restaurant',
    '관광명소': 'spot',
    '공방': 'activity',
    '액티비티': 'activity',
    '숙박': 'accommodation',
    '숙소': 'accommodation',
    '펜션': 'accommodation',
    '호텔': 'accommodation',
}

# Lock&Spin 슬롯 순서 → 기본 카카오 카테고리 매핑
SEQUENCE_TO_CATEGORY = {
    1: '관광명소',   # 오전 명소
    2: '음식점',     # 점심 식사
    3: '카페',       # 오후 카페
    4: '음식점',     # 저녁 식사
}


def _fixed_place_to_place(fp: FixedPlace, region: str):
    """
    FixedPlace(카카오 캐시) → jw Place 모델로 변환/생성.
    place_url을 기준으로 중복 체크합니다.
    """
    from places.models import Place

    jw_category = KAKAO_TO_JW_CATEGORY.get(fp.category, 'spot')
    tag_names = [t.name for t in fp.tags.all()]
    themes_str = ','.join(tag_names)

    # get_or_create 사용 시 빈 URL 등으로 인해 MultipleObjectsReturned 발생 가능. filter.first()로 우회
    if fp.place_url:
        place = Place.objects.filter(place_url=fp.place_url).first()
    else:
        place = Place.objects.filter(name=fp.name, address=fp.address).first()

    if not place:
        place = Place.objects.create(
            name=fp.name,
            address=fp.address,
            region=region,
            place_url=fp.place_url or '',
            latitude=fp.latitude,
            longitude=fp.longitude,
            category=jw_category,
            themes=themes_str,
            image_url=fp.image_url or '',
            description='',
        )
    return place


def _get_coordinates_for_address(address: str, region: str):
    import os
    import requests
    
    kakao_key = os.getenv("KAKAO_REST_API_KEY")
    search_query = address if address else region
    
    if kakao_key and search_query:
        headers = {"Authorization": f"KakaoAK {kakao_key}"}
        url = f"https://dapi.kakao.com/v2/local/search/keyword.json?query={search_query}&size=1"
        try:
            res = requests.get(url, headers=headers, timeout=5)
            if res.status_code == 200:
                docs = res.json().get("documents", [])
                if docs:
                    return float(docs[0].get("y", 0)), float(docs[0].get("x", 0))
        except:
            pass

    # API 실패 또는 결과 없음 시 지역 기본 좌표 반환
    region_coords = {
        '서울': (37.5665, 126.9780),
        '부산': (35.1796, 129.0756),
        '제주': (33.4996, 126.5312),
        '인천': (37.4563, 126.7052),
        '강원': (37.8228, 128.1555),
    }
    
    for r, coords in region_coords.items():
        if r in region or r in search_query:
            return coords
            
    return (37.5665, 126.9780)

def _temp_event_to_place(te, region: str):
    """
    TemporaryEvent(네이버 캐시) → jw Place 모델로 변환/생성.
    link를 기준으로 중복 체크합니다.
    """
    from places.models import Place
    
    # 팝업스토어, 체험 등은 activity로, 전시는 spot으로 분류
    jw_category = 'activity' if '팝업' in te.category or '체험' in te.category else 'spot'
    
    if te.link:
        place = Place.objects.filter(place_url=te.link).first()
    else:
        place = Place.objects.filter(name=f"[행사/전시] {te.name}").first()

    if not place:
        if te.latitude != 0.0 or te.longitude != 0.0:
            lat, lon = te.latitude, te.longitude
        else:
            lat, lon = _get_coordinates_for_address(te.address, region)
            
        place = Place.objects.create(
            name=f"[행사/전시] {te.name}",
            address=te.address or region,
            region=region,
            place_url=te.link or '',
            latitude=lat,
            longitude=lon,
            category=jw_category,
            themes=te.category,
            image_url=te.image_url or '',
            description=f"{te.start_date.strftime('%y.%m.%d')} ~ {te.end_date.strftime('%y.%m.%d')}",
        )
    else:
        # 기존 좌표가 0.0인 데이터가 있다면 업데이트
        if place.latitude == 0.0 and place.longitude == 0.0:
            if te.latitude != 0.0 or te.longitude != 0.0:
                lat, lon = te.latitude, te.longitude
            else:
                lat, lon = _get_coordinates_for_address(te.address, region)
            place.latitude = lat
            place.longitude = lon
            place.save()
            
    return place


def haversine_local(lat1, lon1, lat2, lon2):
    import math
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def get_slot_places_for_course(destination: str, travel_date: str, preferences: str, user, duration_days: int = 1, departure_time: str = "09:00", transportation: str = "public") -> tuple:
    """
    Lock&Spin 코스 생성 시 AI 기반으로 슬롯에 채울 Place 객체들을 반환합니다.

    Returns:
        dict: {
            'spot': [Place, ...],
            'restaurant': [Place, ...],
            'cafe': [Place, ...],
            'activity': [Place, ...],
        }
        tuple: (slot_pool_dict, parsed_json_dict)
    """
    from places.models import Place

    # 사용자 비토 카테고리
    veto_codes = [v.category_code for v in user.veto_categories.all()]

    # 1. Gemini로 자연어 파싱
    parsed = parse_user_request(
        region=destination, 
        travel_date=travel_date, 
        query=preferences or f"{destination} 여행",
        duration_days=duration_days,
        departure_time=departure_time,
        transportation=transportation
    )

    slot_pool = {'spot': [], 'restaurant': [], 'cafe': [], 'activity': [], 'accommodation': []}
    
    # 1단계: 정확한 지역 검색어 추출 (사용자 입력 선호도에서 구/동/역 등의 키워드를 우선 추출)
    import re
    pref_text = preferences or ""
    m = re.search(r'([가-힣]+(?:구|동|역|면|읍|리))|강남|홍대|성수|이태원|건대|신촌|잠실|해운대|서면|종로|명동|여의도|신림|연남|망원|한남|압구정|청담', pref_text)
    exact_dest = m.group(0) if m else (destination.split()[-1] if destination != '랜덤' else None)
    
    # 2단계: 광역 지역 검색어 (첫 2글자. 예: "서울특별시" -> "서울")
    broad_dest = destination[:2] if destination != '랜덤' else None

    exact_coords = None
    if exact_dest:
        exact_coords = _get_coordinates_for_address(exact_dest, broad_dest)

    for jw_cat in ['spot', 'restaurant', 'cafe', 'activity', 'accommodation']:
        qs = Place.objects.filter(category=jw_cat).exclude(category__in=veto_codes)
        
        internal = []
        if exact_dest:
            # 우선 가장 구체적인 지역명으로 검색
            local_qs = qs.filter(address__contains=exact_dest)
            
            # DB에 해당 지역 데이터가 부족한 경우 (5개 미만) 카카오 API로 실시간 수집
            if local_qs.count() < 5:
                kakao_cat = {'spot':'관광명소','restaurant':'음식점','cafe':'카페','accommodation':'숙박'}.get(jw_cat, '액티비티')
                
                # API로 대상 지역을 구체적으로 명시하여 검색
                new_fps = fetch_and_save_kakao_places(exact_dest, kakao_cat, [])
                for fp in new_fps:
                    _fixed_place_to_place(fp, destination)
                
                # DB 수집 후 다시 쿼리
                local_qs = qs.filter(address__contains=exact_dest)
            
            if local_qs.exists():
                # 정확한 지역에 데이터가 충분하면 랜덤하게 섞어서 제공
                internal = list(local_qs.order_by('?')[:15])
            else:
                # 구체적인 지역으로 수집했는데도 없으면, 광역 단위(예: "서울")로 범위 확장하되, 기준점과 가장 가까운 곳 우선 정렬
                broad_qs = qs.filter(address__contains=broad_dest)
                if exact_coords:
                    all_broad = list(broad_qs)
                    all_broad.sort(key=lambda p: haversine_local(p.latitude, p.longitude, exact_coords[0], exact_coords[1]))
                    
                    # 가장 가까운 20개를 추린 뒤, 항상 똑같은 곳만 나오지 않게 약간 섞어서 15개 추출
                    closest_20 = all_broad[:20]
                    random.shuffle(closest_20)
                    internal = closest_20[:15]
                else:
                    internal = list(broad_qs.order_by('?')[:15])
        else:
            internal = list(qs.order_by('?')[:15])
            
        for p in internal:
            if p not in slot_pool[jw_cat]:
                slot_pool[jw_cat].append(p)

    return slot_pool, parsed


def pick_place_for_slot(slot_pool: dict, sequence: int, used_ids: list, target_category: str = None, transportation: str = 'public', last_coords: tuple = None):
    """슬롯 순서 또는 target_category에 맞는 미사용 장소 1개를 선택합니다."""
    if target_category:
        jw_category = target_category
    else:
        category = SEQUENCE_TO_CATEGORY.get(sequence, '관광명소')
        jw_category = KAKAO_TO_JW_CATEGORY.get(category, 'spot')

    candidates = [p for p in slot_pool.get(jw_category, []) if p.id not in used_ids and p.category == jw_category]

    if not candidates:
        if target_category:
            # 타겟 카테고리가 지정되었는데 후보가 없다면 None을 반환하여 외부(views.py)의 카카오 API 긴급 보충(Fallback) 로직이 작동하게 함
            return None
            
        # 전체 풀에서 미사용 장소 선택
        all_places = []
        for places in slot_pool.values():
            all_places.extend(places)
        candidates = [p for p in all_places if p.id not in used_ids and p.category == jw_category]

    if not candidates:
        return None
        
    if last_coords and transportation == 'public' and not target_category:
        # 대중교통일 경우 이전 장소와 가장 가까운 곳 위주로 추천
        candidates.sort(key=lambda p: haversine_local(p.latitude, p.longitude, last_coords[0], last_coords[1]))
        top_n = candidates[:3]
        place = random.choice(top_n)
    else:
        exhibition_candidates = [p for p in candidates if '[행사/전시]' in p.name]
        if exhibition_candidates and random.random() < 0.2:  # 20% 확률로 배정
            place = random.choice(exhibition_candidates)
        else:
            fresh_candidates = [p for p in candidates if '[행사/전시]' not in p.name]
            if not fresh_candidates:
                place = random.choice(candidates)
            else:
                place = random.choice(fresh_candidates)
        
    used_ids.append(place.id)
    return place

def calculate_place_score(place, context: dict) -> float:
    """
    단일 평가 엔진: 특정 장소의 점수를 계산합니다.
    context = {
        'ai_tags': ['가성비', '오션뷰'],
        'user_themes': ['자연', '힐링'],
        'reference_coords': [(lat, lon), (lat, lon)], # 확정된 장소들 좌표
        'transportation': 'public' or 'car'
    }
    """
    import math
    import random
    
    score = 0.0
    place_themes = [t.strip() for t in place.themes.split(',')] if place.themes else []
    
    # 1. AI 맥락(Tags) 매칭 (+8.0)
    ai_tags = context.get('ai_tags', [])
    for t in ai_tags:
        if t in place_themes or t in place.name or t in place.category:
            score += 8.0
            
    # 2. 유저 프로필 매칭 (+5.0)
    user_themes = context.get('user_themes', [])
    for t in user_themes:
        if t in place_themes:
            score += 5.0
            
    # 3. 트렌드 가점 (+2.0)
    if '[행사/전시]' in place.name:
        score += 2.0
        
    # 4. 거리 페널티
    ref_coords = context.get('reference_coords', [])
    transport = context.get('transportation', 'public')
    if ref_coords and place.latitude != 0.0 and place.longitude != 0.0:
        total_dist = 0
        for lat, lon in ref_coords:
            total_dist += haversine_local(place.latitude, place.longitude, lat, lon)
        avg_dist = total_dist / len(ref_coords)
        
        # 패널티: 대중교통은 km당 -8점, 자차는 -1.5점
        penalty_rate = 8.0 if transport == 'public' else 1.5
        score -= (avg_dist * penalty_rate)
        
    # 5. 다양성 (Random Noise)
    score += random.uniform(-3.0, 3.0)
    
    return score
