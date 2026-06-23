import os
import json
import requests
from recommendations.models import AICache


def parse_user_request(region: str, travel_date: str, query: str) -> dict:
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

    prompt = f"""
    당신은 사용자 여행 및 데이트 코스 추천 AI입니다.
    사용자의 여행 지역: "{region}"
    여행 날짜: "{travel_date}"
    사용자의 요구사항: "{query}"

    위 정보를 바탕으로 검색을 위한 카테고리와 태그를 추출하세요.
    특히 "실내데이트" 같은 추상적인 요구사항이 있다면, 이를 "실내", "데이트", "공방", "전시회", "카페" 등
    실제 장소 검색에 유리한 구체적 카테고리와 태그로 분해해 주세요.

    응답은 반드시 유효한 JSON 문자열이어야 하며, 마크다운(```json 등)을 포함하지 마세요.

    {{
      "region": "{region}",
      "travel_date": "{travel_date}",
      "fixed_places": [
         {{"category": "카페", "tags": ["실내", "분위기있는"]}},
         {{"category": "음식점", "tags": ["데이트"]}},
         {{"category": "관광명소", "tags": ["힐링"]}}
      ],
      "temporary_events": [
         {{"category": "팝업스토어", "tags": ["실내"]}},
         {{"category": "전시회", "tags": ["미술"]}}
      ]
    }}

    고정적 장소(음식점, 카페, 숙소, 공방, 액티비티, 관광명소, 수목원 등)는 fixed_places에,
    일시적 행사(팝업, 전시회, 행사, 공연, 축제 등)는 temporary_events에 분류하세요.
    요구사항에 부합하는 카테고리 종류를 유추해서 2~4개씩 배열에 담아주세요.
    """

    gms_key = os.getenv("GMS_API_KEY", "S15P02AC08-8f77e8e6-255f-4ce7-9677-d72295149548")
    url = "https://gms.ssafy.io/gmsapi/generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-lite:generateContent"

    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": gms_key
    }

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.1}
    }

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
        print(f"Gemini API Error: {e}")
        return _fallback_parse(region, travel_date, query)


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
