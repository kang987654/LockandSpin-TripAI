import os
import json
import requests
from recommendations.models import AICache

# ==============================================================================
# [발표 캡처용] AI 프롬프트 엔지니어링 영역
# 이 영역의 프롬프트들을 활용하여 생성형 AI(Gemini)의 논리와 데이터 출력을 정교하게 제어합니다.
# ==============================================================================

# 1. 여행 취향 및 요구사항 자연어 파싱 프롬프트
USER_REQUEST_PARSE_PROMPT = """
# Role
당신은 즉흥적이고 유연한 여행을 선호하는 여행자들을 위해 최적의 일정 뼈대를 설계해 주는 'AI 트래블 디렉터'입니다. 당신의 핵심 목표는 분 단위의 빡빡한 계획을 강요하는 것이 아니라, 현지 상황에 따라 언제든 일정을 수정할 수 있도록 여유 공간(Buffer)이 충분한 '감각적이고 직관적인 가이드라인'을 제공하는 것입니다.

# Input Variables
- Destination (장소): {region}
- Vehicle (차량 유무): {transportation}
- Departure Time (출발 시간): {departure_time}
- Travel Dates (여행 날짜): {travel_date}
- Duration (여행 기간): {duration_days}일
- Theme (여행 테마): {query}

# Core Logic 1: 조건별 동선 및 일정 설계 (Strict Routing)
1. 출발 시간 (Departure Time) 반영:
   - 1일 차 일정은 반드시 [Departure Time] + [장소까지의 예상 이동 시간] 이후부터 시작합니다.
   - 늦은 오후나 저녁 도착인 경우, 무리한 스팟 방문을 배제하고 숙소 체크인, 가벼운 저녁 식사 및 야경/산책 위주로만 일정을 구성합니다.

2. 차량 유무 (Vehicle) 반영에 따른 동선 제어:
   - [대중교통/도보]: (가장 중요) 여행 피로도를 최소화하기 위해 '동일한 구/동' 또는 '단일 지하철/버스 노선' 내에서 일정이 해결되도록 스팟을 강하게 묶습니다(Clustering). 스팟 간 이동 시간은 도보 15분, 대중교통 20분 이내로 엄격히 제한합니다. 환승이 2회 이상 필요한 복잡한 동선은 절대 배제하며, 무거운 짐을 고려해 터미널/기차역/숙소 주변을 중심으로 동선을 짭니다.
   - [자차/렌트카]: 스팟 간 이동 거리 제한을 여유롭게 두고(최대 40~50분), 드라이브 코스, 외곽의 대형 카페, 주차 공간이 확실히 확보된 장소를 적극적으로 포함합니다.

# Core Logic 2: 숙소 (Accommodation) 배치 규칙
- 당일치기를 제외한 모든 일정에는 매일 1회의 숙소(Check-in/Rest) 일정을 베이스로 필수 삽입합니다.
- 배치 타이밍: 오후 일정과 저녁 식사 사이(16:00~18:00)에 잠시 들러 짐을 풀고 휴식하거나, 일정 마무리 직전(20:00 이후)에 배치합니다.
- 숙소 위치 기준: 1일 차 메인 활동 지역과 2일 차 오전 활동 지역의 중간 지점, 대중교통 이용 시 대중교통 거점(역/터미널) 근처로 상정합니다.

# Core Logic 3: 기간별 베이스 캠프 (Day-by-Day Blueprint)
[당일치기]
- 시작: 도착 시점 이후
- 흐름: 메인 테마 스팟 1 -> 점심 -> 메인 테마 스팟 2 -> 카페 -> 저녁 후 귀가

[1박 2일]
- 1일 차: 도착 -> 테마 몰입 스팟 -> [숙소 체크인 및 휴식] -> 로컬 저녁 식사 -> 가벼운 야간 산책
- 2일 차: 여유로운 브런치 -> 터미널/역/IC 근처 스팟 1곳 -> 귀가

[2박 3일]
- 1일 차: 도착 -> 주변 탐색 -> [숙소 체크인] -> 저녁 식사
- 2일 차(메인): 오전 메인 스팟 -> 점심 -> 오후 액티비티/투어 -> [숙소 휴식] -> 저녁 식사 -> 야간 핫플레이스
- 3일 차: 체크아웃 -> 뷰가 좋은 테마 카페 혹은 기념품/소품샵 -> 귀가

[3박 4일]
- 1일 차: 여유로운 도착 및 [숙소 체크인], 분위기 적응
- 2일 차: 가장 활동적인 테마 스팟 집중 공략
- 3일 차: [여백의 날] 오전을 비워두어 늦잠을 허용하거나, 한적한 근교로 빠져 템포를 늦추는 힐링 일정 배치
- 4일 차: 체크아웃 -> 아쉬움을 달래는 스팟 1곳 -> 점심 후 귀가

# Output Instruction
1. 빡빡한 스케줄은 피하고, 스팟 간 충분한 여유 시간(Buffer)을 두세요. 
2. 각 스팟마다 "왜 이 장소를 추천하는지" 1줄 이유를 포함하세요.
3. 여행자가 변덕을 부릴 수 있도록, 일정 중 최소 1~2곳에는 대체 가능한 '옵션(Alternative)'을 짧게 제안하세요.
4. [매우 중요] 각 일차별 `schedules` 배열의 길이는 반드시 'Core Logic 3'에 제시된 화살표(->) 단계 수에 맞춰 최소화하세요. (예: 1박 2일의 1일 차는 3~4개의 장소만 추천).
5. [매우 중요] "도착", "주변 탐색", "귀가", "여유로운 브런치(장소 미정)" 처럼 구체적인 장소가 없는 단순 상태나 이동은 `schedules` 목록에 포함하지 마세요. 오직 실제 방문할 식당, 카페, 명소, 숙소만 배열에 넣으세요.
6. 클라이언트 애플리케이션에서 파싱하여 모던한 UI로 렌더링할 수 있도록 반드시 아래의 JSON 포맷을 엄격하게 지켜서 출력하세요. 마크다운 기호(```json)를 포함하여 응답하세요.

# JSON Output Format (Strict)
```json
{{
  "itinerary_summary": {{
    "title": "AI가 추천하는 여행 요약 타이틀",
    "total_days": "{duration_days}일",
    "theme_matched": ["매칭된", "핵심", "키워드"]
  }},
  "daily_plans": [
    {{
      "day": 1,
      "date": "{travel_date}",
      "route_summary": "1일 차 동선 요약 (예: 도착 및 해운대구 중심 탐색)",
      "schedules": [
        {{
          "time_slot": "오전/오후/저녁",
          "activity_type": "Spot / Meal / Cafe / Accommodation",
          "location_name": "추천 장소 이름",
          "reason": "이 장소를 추천하는 1줄 이유",
          "alternative_option": "기분에 따라 변경 가능한 대체 옵션 1개 (없으면 null)"
        }}
      ]
    }}
  ]
}}
```
"""

# 2. 생성된 코스 피드백 및 조언 작성 프롬프트
COURSE_REVIEW_SYSTEM_PROMPT = """
당신은 대한민국 최고의 여행 플래너입니다.
아래는 당신이 구성한 데이트/여행 코스 목록입니다.

[코스 정보]
목적지: {destination}
테마/취향: {preferences}
방문 장소들: {place_list_text}

이 코스에 대해 아래의 3가지 항목으로 나누어 깔끔하게 추론하고 평가한 내용을 적어주세요.
가독성을 위해 마크다운 헤더(###)와 글머리 기호(-)를 적절히 사용해 주세요.

**[매우 중요]**
'안녕하세요', '대한민국 최고의 여행 플래너로서' 같은 불필요한 인사말이나 서론은 절대 쓰지 마세요.
곧바로 `### 1. 전체적인 여행의 내용 및 평가` 부터 시작해야 합니다.

### 1. 전체적인 여행의 내용 및 평가
- 코스의 주된 테마와 일정의 흐름 요약
- 이 코스만의 특별한 장점

### 2. 전체적인 예산지출 예산안
- 식비, 교통, 입장료 등을 고려한 대략적인 예상 비용
- 예산을 아낄 수 있는 꿀팁

### 3. 총 평가
- 이 코스를 누구에게 추천하는지
- 여행 시 주의할 점이나 마무리 코멘트
"""


# 3. 밥 메뉴 추천 프롬프트
FOOD_RECOMMENDATION_PROMPT = """
당신은 최고의 미식가이자 식당 추천 AI입니다.
사용자가 입력한 지역과 '오늘 먹고 싶은 음식(기분/상황)'을 바탕으로,
1. 어떤 종류의 음식(한식, 양식, 일식, 중식, 분식, 카페/디저트 등)이 어울릴지 카테고리를 추론하세요.
2. 카카오맵에서 검색하기 가장 좋은 '검색 키워드(지역명 + 구체적인 메뉴명)'를 생성하세요. (예: "강남역 얼큰한 국물" 보다는 "강남역 짬뽕" 또는 "강남역 국밥"이 좋습니다)
3. 왜 이 메뉴를 추천하는지 사용자에게 친근하고 재치 있게 전달할 멘트(50자 내외)를 작성하세요.

[사용자 입력]
지역: "{region}"
원하는 음식/기분: "{preference}"

응답은 반드시 아래 형식의 유효한 JSON 문자열이어야 하며, 마크다운(```json 등)을 포함하지 마세요.
{{
    "category": "추론된 카테고리 (예: 중식)",
    "search_keyword": "지역명 + 메뉴 (예: 강남역 마라탕)",
    "recommend_message": "비 오는 날엔 역시 얼큰한 마라탕이죠! 스트레스가 확 풀릴 거예요."
}}
"""


def generate_course_comment(destination: str, preferences: str, places: list) -> str:
    """
    생성된 코스 목록을 바탕으로 AI가 한줄평 코멘트를 생성합니다.
    """
    place_list_text = ", ".join([f"{p.name}({p.category})" for p in places])
    prompt = COURSE_REVIEW_SYSTEM_PROMPT.format(
        destination=destination,
        preferences=preferences,
        place_list_text=place_list_text
    )

    gms_key = os.getenv("GMS_API_KEY")
    url = "https://gms.ssafy.io/gmsapi/generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-lite:generateContent"
    headers = {"Content-Type": "application/json", "x-goog-api-key": gms_key}
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.7}
    }

    try:
        res = requests.post(url, headers=headers, json=payload, timeout=10)
        res.raise_for_status()
        raw_text = res.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
        return raw_text
    except Exception as e:
        print(f"Gemini API Error (Comment): {e}")
        return "멋진 장소들로 알차게 구성된 여행 코스입니다!"


def parse_user_request(region: str, travel_date: str, query: str, duration_days: int = 1, departure_time: str = "09:00", transportation: str = "public") -> dict:
    """
    사용자의 요청을 Gemini API를 통해 분석하여 구조화된 데이터로 반환합니다.
    AICache를 활용하여 동일 쿼리 반복 호출을 방지합니다.
    """
    cache_key = f"{region}_{travel_date}_{query}".strip()
    try:
        cached = AICache.objects.get(query_key=cache_key)
        return cached.parsed_result
    except AICache.DoesNotExist:
        pass

    prompt = USER_REQUEST_PARSE_PROMPT.format(
        region=region,
        travel_date=travel_date,
        duration_days=duration_days,
        departure_time=departure_time,
        transportation=transportation,
        query=query
    )

    gms_key = os.getenv("GMS_API_KEY")
    url = "https://gms.ssafy.io/gmsapi/generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-lite:generateContent"

    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": gms_key
    }

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.1}
    }

    import time
    for attempt in range(3):
        try:
            res = requests.post(url, headers=headers, json=payload, timeout=15)
            res.raise_for_status()
            res_data = res.json()
            raw_text = res_data["candidates"][0]["content"]["parts"][0]["text"].strip()

            if raw_text.startswith("```json"):
                raw_text = raw_text[7:].strip()
                if raw_text.endswith("```"):
                    raw_text = raw_text[:-3].strip()
            elif raw_text.startswith("```"):
                raw_text = raw_text[3:].strip()
                if raw_text.endswith("```"):
                    raw_text = raw_text[:-3].strip()

            data = json.loads(raw_text)

            if "daily_plans" in data:
                AICache.objects.get_or_create(query_key=cache_key, defaults={"parsed_result": data})

            return data

        except Exception as e:
            print(f"Gemini API Error (Attempt {attempt+1}/3): {e}")
            if attempt == 2:
                return _fallback_parse(region, travel_date, query)
            time.sleep(1)

def extract_realtime_keywords(query: str) -> dict:
    """
    유저가 입력한 텍스트에서 실시간으로 추천 해시태그용 키워드와 어울리는 여행 제목을 추출합니다.
    """
    if not query.strip():
        return {"title": "", "tags": []}
        
    prompt = f"""다음 사용자의 여행 요구사항을 바탕으로 센스있는 '여행 제목'과 핵심이 되는 '태그 3~5개'를 추출하세요.
요구사항: {query}

응답은 반드시 아래 형식의 유효한 JSON 문자열이어야 하며, 마크다운(```json 등)을 포함하지 마세요.
{{
    "title": "비오는 날 제주도 실내 데이트",
    "tags": ["실내", "비오는날", "데이트", "맛집"]
}}
"""
    
    gms_key = os.getenv("GMS_API_KEY")
    url = "https://gms.ssafy.io/gmsapi/generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-lite:generateContent"
    headers = {"Content-Type": "application/json", "x-goog-api-key": gms_key}
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.4}
    }
    try:
        res = requests.post(url, headers=headers, json=payload, timeout=5)
        res.raise_for_status()
        raw_text = res.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
        # 마크다운 제거
        if raw_text.startswith("```json"):
            raw_text = raw_text[7:]
        if raw_text.endswith("```"):
            raw_text = raw_text[:-3]
        
        import json
        data = json.loads(raw_text.strip())
        return data
    except Exception as e:
        print(f"Realtime extraction error: {e}")
        return {"title": "", "tags": []}

def _fallback_parse(region: str, travel_date: str, query: str) -> dict:
    """Gemini API 실패 시 키워드 기반 폴백 파싱"""
    return {
        "itinerary_summary": {
            "title": f"{region} 추천 코스",
            "total_days": "1일",
            "theme_matched": ["추천", "여행"]
        },
        "daily_plans": [
            {
                "day": 1,
                "date": travel_date,
                "route_summary": f"{region} 알짜배기 당일치기 코스",
                "schedules": [
                    {
                        "time_slot": "오전",
                        "activity_type": "Spot",
                        "location_name": f"{region} 인기 명소",
                        "reason": "가장 유명한 랜드마크입니다.",
                        "alternative_option": None
                    },
                    {
                        "time_slot": "점심",
                        "activity_type": "Meal",
                        "location_name": f"{region} 맛집",
                        "reason": "현지인 추천 맛집입니다.",
                        "alternative_option": None
                    },
                    {
                        "time_slot": "오후",
                        "activity_type": "Cafe",
                        "location_name": f"{region} 카페",
                        "reason": "경치가 좋은 카페입니다.",
                        "alternative_option": None
                    }
                ]
            }
        ]
    }

def recommend_food_menu(region: str, preference: str) -> dict:
    """사용자 기분/원하는 메뉴 기반으로 식당 1곳 추천"""
    prompt = FOOD_RECOMMENDATION_PROMPT.format(region=region, preference=preference)
    gms_key = os.getenv("GMS_API_KEY")
    url = "https://gms.ssafy.io/gmsapi/generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-lite:generateContent"
    headers = {"Content-Type": "application/json", "x-goog-api-key": gms_key}
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.7}
    }
    
    try:
        res = requests.post(url, headers=headers, json=payload, timeout=10)
        res.raise_for_status()
        raw_text = res.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
        if raw_text.startswith("```json"): raw_text = raw_text[7:]
        if raw_text.endswith("```"): raw_text = raw_text[:-3]
        
        data = json.loads(raw_text.strip())
        
        # 카카오 API로 검색
        from recommendations.services.kakao_service import fetch_and_save_kakao_places
        from recommendations.services.recommendation_service import _fixed_place_to_place
        from places.models import Place
        
        new_fps = fetch_and_save_kakao_places(data['search_keyword'], "", [])
        
        place_data = None
        if new_fps:
            p = _fixed_place_to_place(new_fps[0], region)
            if p:
                place_data = {
                    "id": p.id,
                    "name": p.name,
                    "address": p.address,
                    "image_url": p.image_url,
                    "category": p.get_category_display(),
                    "place_url": p.place_url
                }
                
        return {
            "ai_analysis": data,
            "place": place_data
        }
    except Exception as e:
        print(f"Food recommendation error: {e}")
        return {"error": str(e)}
