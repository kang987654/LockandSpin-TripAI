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
당신은 사용자 여행 및 데이트 코스 추천 AI입니다.
사용자의 여행 지역: "{region}"
여행 날짜: "{travel_date}" (총 {duration_days}일 일정)
출발 시간: "{departure_time}"
교통 수단: "{transportation}"
사용자의 요구사항: "{query}"

위 정보를 바탕으로 검색을 위한 카테고리와 태그를 추출하고, 여행 일자별(daily_slots)로 필요한 슬롯의 구조를 설계하세요.

[지시사항]
1. 이제부터 당신(AI)이 일정을 **처음부터 끝까지 주도적으로 완벽하게 계획**해야 합니다. 사용자가 입력한 테마와 정보를 분석하여 완벽한 동선을 세우세요.
2. 당신이 세운 계획(음식점, 카페, 숙소, 놀거리 등)을 바탕으로, 거리와 이동수단({transportation})을 종합적으로 계산하여 **가야 할 장소들의 구체적 키워드(지역명+장소명 또는 지역명+업종)**를 정하세요. 
3. **[매우 중요]** 정해진 장소 키워드들은 **반드시 `daily_slots`에 생성된 총 슬롯 개수만큼 전부 `specific_places` 배열에 순서대로 채워 넣어야 합니다.** (백엔드에서 임의로 랜덤 배정하지 못하도록 당신이 전부 지정해야 합니다.)
4. 장소를 결정할 때 다음의 **우선순위**를 엄격하게 지키세요:
   - **1순위: 위치 및 이동 동선** (첫 장소나 유저가 요구한 특정 동네를 중심으로, 장소 간 이동 거리를 최소화하는 최적의 동선 흐름을 만드세요)
   - **2순위: 사용자의 니즈** (유저가 요구한 카페, 만화카페, 공방 등의 특수 목적)
   - **3순위: 이동수단** (도보/대중교통이면 무조건 가까운 곳, 차량이면 동선이 조금 길어도 허용)
5. 여행 기간({duration_days}일)과 출발 시간({departure_time})을 고려하여 `daily_slots`를 동적으로 구성하세요. 
   - **[숙박 필수 규칙]** 1박 이상의 일정({duration_days}일 > 1)일 경우, 마지막 날을 제외한 매일 저녁 일정 마지막에는 반드시 **"숙소"**(Accommodation) 슬롯을 포함시키세요.
   - 1일차 출발 시간이 오후(예: 14:00)라면 오전 일정은 빼고 점심/카페/저녁 등으로 알맞게 축소하세요.

응답은 반드시 아래 형식의 유효한 JSON 문자열이어야 하며, 마크다운(```json 등)을 포함하지 마세요.

{{
    "region": "{region}",
    "specific_places": ["애월 카페", "애월 해변 관광명소", "애월 흑돼지 음식점", "애월 오션뷰 숙소", "애월 해물라면 음식점", "애월 소품샵 관광명소", "애월 디저트 카페"],
    "daily_slots": {{
        "1": ["카페", "관광명소", "음식점", "숙소"],
        "2": ["음식점", "관광명소", "카페"]
    }},
    "fixed_places": [
        {{"category": "카페", "tags": ["실내", "분위기있는"]}},
        {{"category": "음식점", "tags": ["데이트"]}},
        {{"category": "숙소", "tags": ["오션뷰"]}}
    ],
    "temporary_events": [
        {{"category": "팝업스토어", "tags": ["실내"]}}
    ]
}}

고정적 장소(음식점, 카페, 숙소, 공방, 액티비티, 관광명소 등)는 fixed_places에,
일시적 행사(팝업, 전시회, 공연, 축제 등)는 temporary_events에 분류하세요.
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

            if "fixed_places" in data or "temporary_events" in data:
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
    fallback_data = {
        "region": region,
        "travel_date": travel_date,
        "fixed_places": [],
        "temporary_events": []
    }

    tags = ["데이트"]
    if "실내" in query or "비" in query:
        tags.append("실내")
    if "조용" in query:
        tags.append("조용한")
    if "가성비" in query:
        tags.append("가성비")
    if "힐링" in query:
        tags.append("힐링")

    if "카페" in query or "커피" in query or "디저트" in query:
        fallback_data["fixed_places"].append({"category": "카페", "tags": tags})
    if "밥" in query or "식당" in query or "맛집" in query or "음식" in query:
        fallback_data["fixed_places"].append({"category": "음식점", "tags": tags})
    if "공방" in query or "만들기" in query:
        fallback_data["fixed_places"].append({"category": "공방", "tags": tags})
    if "관광" in query or "명소" in query or "여행" in query:
        fallback_data["fixed_places"].append({"category": "관광명소", "tags": tags})

    if "전시" in query or "미술" in query:
        fallback_data["temporary_events"].append({"category": "전시회", "tags": []})
    if "팝업" in query or "스토어" in query:
        fallback_data["temporary_events"].append({"category": "팝업스토어", "tags": []})

    # 아무 키워드도 없을 때 기본값
    if not fallback_data["fixed_places"] and not fallback_data["temporary_events"]:
        fallback_data["fixed_places"] = [
            {"category": "관광명소", "tags": tags},
            {"category": "음식점", "tags": tags},
            {"category": "카페", "tags": tags},
        ]

    return fallback_data
