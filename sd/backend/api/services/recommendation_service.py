from datetime import datetime
from api.models import FixedPlace, TemporaryEvent
from .ai_service import parse_user_request
from .kakao_service import fetch_and_save_kakao_places
from .naver_service import fetch_and_save_naver_events

def get_recommendations(region: str, travel_date: str, query: str):
    # 1. 자연어 파싱 (Gemini)
    parsed_data = parse_user_request(region, travel_date, query)
    
    if "error" in parsed_data:
        return {"error": parsed_data["error"]}
        
    ai_region = parsed_data.get("region", region)
    
    # 여행 날짜 파싱
    target_date = datetime.now().date()
    try:
        if travel_date:
            target_date = datetime.strptime(travel_date, "%Y-%m-%d").date()
    except:
        pass

    fixed_places = parsed_data.get("fixed_places", [])
    temporary_events = parsed_data.get("temporary_events", [])
    
    results = {
        "region": ai_region,
        "travel_date": str(target_date),
        "recommendations": {
            "fixed": [],
            "temporary": []
        }
    }
    
    # 2. 고정 장소 처리 (트랙 A)
    for fp in fixed_places:
        category = fp.get("category", "")
        tags = fp.get("tags", [])
        
        # DB 조회
        db_places = FixedPlace.objects.filter(region=ai_region, category=category)
        
        # 태그 매칭 로직
        scored_places = []
        for p in db_places:
            p_tags = set([t.name for t in p.tags.all()])
            match_count = len(set(tags).intersection(p_tags))
            scored_places.append((match_count, p))
            
        scored_places.sort(key=lambda x: x[0], reverse=True)
        valid_places = [p[1] for p in scored_places if p[0] > 0]
        
        # 부족하면 카카오 API 호출
        if len(valid_places) < 3:
            new_places = fetch_and_save_kakao_places(ai_region, category, tags)
            for np in new_places:
                if np not in valid_places:
                    valid_places.append(np)
        
        for p in valid_places[:3]:
            # 중복 체크
            if not any(item['id'] == p.id for item in results["recommendations"]["fixed"]):
                results["recommendations"]["fixed"].append({
                    "id": p.id,
                    "name": p.name,
                    "category": p.category,
                    "tags": [t.name for t in p.tags.all()],
                    "image_url": p.image_url,
                    "link": p.place_url
                })
            
    # 3. 일시적 행사 처리 (트랙 B)
    for te in temporary_events:
        category = te.get("category", "")
        
        # 날짜 조건 DB 조회
        db_events = TemporaryEvent.objects.filter(
            region=ai_region,
            category=category,
            start_date__lte=target_date,
            end_date__gte=target_date
        )
        
        valid_events = list(db_events)
        
        if len(valid_events) < 2:
            new_events = fetch_and_save_naver_events(ai_region, category)
            for ev in new_events:
                if ev.start_date <= target_date <= ev.end_date and ev not in valid_events:
                    valid_events.append(ev)
                    
        for e in valid_events[:2]:
            if not any(item['name'] == e.name for item in results["recommendations"]["temporary"]):
                results["recommendations"]["temporary"].append({
                    "name": e.name,
                    "category": e.category,
                    "dates": f"{e.start_date} ~ {e.end_date}",
                    "image_url": e.image_url,
                    "link": e.link
                })

    return results
