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
    '숙소': 'activity',
    '펜션': 'activity',
    '호텔': 'activity',
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

    slot_pool = {'spot': [], 'restaurant': [], 'cafe': [], 'activity': []}

    # 2. 고정 장소 처리 (트랙 A - 카카오 API)
    for fp_info in parsed.get('fixed_places', []):
        category = fp_info.get('category', '')
        tags = fp_info.get('tags', [])
        jw_category = KAKAO_TO_JW_CATEGORY.get(category, 'spot')

        if jw_category in veto_codes:
            continue

        # DB 먼저 조회
        db_places = FixedPlace.objects.filter(region=destination, category=category)[:5]
        api_needed = db_places.count() < 3

        places_from_db = [_fixed_place_to_place(fp, destination) for fp in db_places]

        if api_needed:
            # 카카오 API 호출
            new_fps = fetch_and_save_kakao_places(destination, category, tags)
            places_from_api = [_fixed_place_to_place(fp, destination) for fp in new_fps]
            merged = list({p.id: p for p in places_from_db + places_from_api}.values())
        else:
            merged = places_from_db

        for p in merged:
            if p not in slot_pool[jw_category]:
                slot_pool[jw_category].append(p)

    # 3. 일시적 행사 처리 (트랙 B - 네이버 API) — 부족한 카테고리 보완용
    from datetime import datetime
    try:
        target_date = datetime.strptime(travel_date, "%Y-%m-%d").date()
    except Exception:
        target_date = datetime.now().date()

    from recommendations.models import TemporaryEvent
    for te_info in parsed.get('temporary_events', []):
        category = te_info.get('category', '')
        jw_category = 'activity' if '팝업' in category or '체험' in category else 'spot'
        
        if jw_category in veto_codes:
            continue

        db_events = TemporaryEvent.objects.filter(
            region=destination,
            category=category,
            start_date__lte=target_date,
            end_date__gte=target_date
        )[:5]
        
        events_from_db = [_temp_event_to_place(te, destination) for te in db_events]
        
        if len(events_from_db) < 2:
            new_tes = fetch_and_save_naver_events(destination, category)
            # 날짜 필터링
            valid_tes = [te for te in new_tes if te.start_date <= target_date <= te.end_date]
            events_from_api = [_temp_event_to_place(te, destination) for te in valid_tes]
            merged_events = list({p.id: p for p in events_from_db + events_from_api}.values())
        else:
            merged_events = events_from_db
            
        for p in merged_events:
            if p not in slot_pool[jw_category]:
                slot_pool[jw_category].append(p)

    # 4. 풀이 비어있는 카테고리는 내부 DB에서 보완 (지역 필터 필수)
    dest_prefix = destination[:2] if destination != '랜덤' else None

    for jw_cat in ['spot', 'restaurant', 'cafe', 'activity']:
        if len(slot_pool[jw_cat]) < 2:
            qs = Place.objects.filter(category=jw_cat).exclude(category__in=veto_codes)
            if dest_prefix:
                local_qs = qs.filter(address__contains=dest_prefix)
                if local_qs.exists():
                    qs = local_qs
                else:
                    # 지역에 정 없으면 카카오 API로 긴급 수집
                    kakao_cat = '관광명소' if jw_cat == 'spot' else '음식점' if jw_cat == 'restaurant' else '카페' if jw_cat == 'cafe' else '액티비티'
                    new_fps = fetch_and_save_kakao_places(destination, kakao_cat, [])
                    for fp in new_fps:
                        _fixed_place_to_place(fp, destination)
                    
                    qs = Place.objects.filter(category=jw_cat, address__contains=dest_prefix).exclude(category__in=veto_codes)
            
            internal = list(qs.order_by('?')[:5])
            for p in internal:
                if p not in slot_pool[jw_cat]:
                    slot_pool[jw_cat].append(p)

    return slot_pool, parsed


def pick_place_for_slot(slot_pool: dict, sequence: int, used_ids: list, target_category: str = None):
    """슬롯 순서 또는 target_category에 맞는 미사용 장소 1개를 선택합니다."""
    if target_category:
        jw_category = target_category
    else:
        category = SEQUENCE_TO_CATEGORY.get(sequence, '관광명소')
        jw_category = KAKAO_TO_JW_CATEGORY.get(category, 'spot')

    candidates = [p for p in slot_pool.get(jw_category, []) if p.id not in used_ids]

    if not candidates:
        # 전체 풀에서 미사용 장소 선택
        all_places = []
        for places in slot_pool.values():
            all_places.extend(places)
        candidates = [p for p in all_places if p.id not in used_ids]

    if not candidates:
        return None
        
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
