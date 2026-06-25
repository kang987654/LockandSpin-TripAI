# 재사용 가능한 AI/웹 개발 스킬셋 (Reusable Skills)

이 문서는 본 프로젝트를 통해 검증된 핵심 로직과 디자인 패턴들을 스킬(Skill) 단위로 쪼개어 정의한 것입니다. 다른 웹 프로젝트나 AI 기반 추천 시스템을 구축할 때 참고하여 빠르게 도입할 수 있습니다.

## Skill 1: 하이브리드 추천 엔진 로직 (Hybrid AI Recommendation Engine)
**설명:** LLM의 할루시네이션(환각) 문제를 해결하기 위해 AI의 '기획력'과 자체 DB의 '정확성'을 결합하는 로직입니다.
- **Workflow:**
  1. AI에게 지역, 테마, 날짜를 주고 구체적인 장소가 아닌 **"장소 카테고리(예: 관광명소, 카페, 식당) 및 테마 키워드의 배열"**만을 결과로 받음 (구조화된 JSON/배열 추출).
  2. 시스템(백엔드)에서 이 뼈대 배열을 들고 실제 데이터베이스를 쿼리함.
  3. DB에 데이터가 부족할 경우 즉시 Kakao Local API, Naver Search API를 찔러서 실제 데이터를 확보.
  4. 확보된 실제 장소를 **점수 기반(거리/취향 일치도) 알고리즘**으로 평가해 가장 높은 점수의 실존 장소를 최종 매핑.

## Skill 2: 맵/동선 무결성 보장 알고리즘 (Location Drifting Prevention)
**설명:** 장소를 무작위로 추천하여 동선이 전국 방방곡곡으로 튀는 현상을 막기 위한 가중치 기반 스코어링 스킬입니다.
- **구현 방식:**
  - **Anchor Point (기준점) 설정:** 그날 일정 중 이미 확정(Lock)되었거나 사용자가 명시한 지역의 `[위도, 경도]`를 기준 좌표 리스트로 설정.
  - **거리 가중치:** 후보 장소들과 앵커 포인트들의 거리를 계산해, 거리가 멀어질수록 점수에 막대한 페널티(Penalty)를 부여.
  - **지역명 매칭:** 장소의 주소(`address`) 속성에 기준 목적지(예: `강남구`) 문자열이 포함되어 있으면 가산점 부여.

## Skill 3: Try-before-you-buy (점진적 가입 유도 UX)
**설명:** 비회원(익명) 사용자에게도 서비스의 가치를 먼저 제공한 뒤, 데이터 저장 시점에 자연스럽게 가입을 유도하는 패턴입니다.
- **구현 방식:**
  - DB 모델 설계 시 작성자 속성을 `user = models.ForeignKey(..., null=True, blank=True)`로 열어둠.
  - 폼 제출 시 비회원이면 `user=null` 상태로 임시 데이터(Draft)를 정상 생성 및 화면 반환.
  - 프론트엔드 라우터에서 해당 상세 페이지의 `requiresAuth` 가드를 해제하여 비회원 열람 허용.
  - 유저가 '저장/확정' 버튼 클릭 시, 
    1) 현재 페이지 주소를 `?redirect=/current/path`로 달아 `/login`으로 튕겨냄.
    2) 가입/로그인 완료 직후 `redirect` 주소로 복귀.
    3) 백엔드의 `claim` API를 호출해 `user=null`이었던 데이터를 `user=현재로그인유저`로 소유권 이전.

## Skill 4: 프론트엔드/백엔드 이중 권한 동기화 (Dual Permission Sync)
**설명:** 커뮤니티나 공유 기능에서 타인의 문서를 수정할 수 없도록 UI와 서버 양쪽을 완벽히 차단하는 기법입니다.
- **Frontend (Vue.js):** 
  - 상태 관리소(Pinia)에서 현재 문서의 작성자 정보와 내 인증 정보(`currentUser`)를 비교하는 `hasEditPermission` (Computed Property) 생성.
  - 편집/삭제/재생성 버튼 등 위험한 액션 UI를 단순히 `disabled` 처리하는 것이 아니라 `v-if="hasEditPermission"`으로 DOM 자체에서 렌더링 배제.
- **Backend (DRF):**
  - 조회(GET) 요청에는 `AllowAny`를 열어두되, 수정/삭제(PUT, DELETE, POST 특정 액션) 요청 시에는 `IsAuthenticated`를 검증하고, 나아가 `get_object()` 레벨에서 작성자 일치 여부를 검증해 403/404를 반환.

## Skill 5: Axios 인증 헤더 안전 처리 (Safe JWT Headers)
**설명:** 토큰 기반 인증 시 발생할 수 있는 잠재적 401(Unauthorized) 에러를 방지합니다.
- **구현 방식:**
  - 토큰을 가져와 헤더에 주입하는 함수 작성 시, 무조건 `Authorization` 헤더를 생성하지 않음.
  - `if (token.value) { return { Authorization: Bearer ${token.value} } }` 처럼 값이 유효할 때만 헤더를 세팅하고, 비회원일 경우 순수한 빈 객체(`{}`)를 반환해 백엔드가 올바르게 익명 사용자로 판단하게 유도함.

---

# [관통PJT 제출 및 발표 자료 캡처용] AI 구현 상세 내역

명세서 요구사항에 따른 **생성형 AI(Gemini 3.5 Flash)** 활용 로직 및 데이터 구성 내역입니다. 아래 코드를 캡처하여 발표 자료(PPT) 및 소스코드 제출 시 활용하십시오.

## 1. 프롬프트 캡처 (Prompt Engineering)
여행자의 취향과 일정 제약 조건을 분석하여 AI가 환각 없이 유효한 카테고리 뼈대만 반환하도록 강제하는 프롬프트입니다. (`backend/recommendations/services/ai_service.py`)

```python
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
   - [대중교통/도보]: 여행 피로도를 최소화하기 위해 '동일한 구/동' 또는 '단일 지하철/버스 노선' 내에서 일정이 해결되도록 스팟을 강하게 묶습니다(Clustering). 환승이 2회 이상 필요한 복잡한 동선은 배제합니다.
   - [자차/렌트카]: 스팟 간 이동 거리 제한을 여유롭게 두고, 외곽의 대형 카페, 주차 공간이 확보된 장소를 포함합니다.

# Core Logic 2: 숙소 (Accommodation) 배치 규칙
- 당일치기를 제외한 모든 일정에는 매일 1회의 숙소(Check-in/Rest) 일정을 베이스로 필수 삽입합니다.

# Output Instruction
1. [매우 중요] 각 스팟마다 구체적인 상호명(`location_name`)을 억지로 지어내지 마세요. 무조건 빈 문자열("")로 두어 백엔드 자체 DB 검색을 유도하세요.
2. [매우 중요] 대신, 해당 스팟에 어울리는 감성 및 특성 태그(`tags`)를 추출해 주세요.
3. 클라이언트 애플리케이션에서 파싱할 수 있도록 반드시 JSON 포맷을 엄격하게 지켜서 출력하세요.

# JSON Output Format (Strict)
```json
{{
  "daily_plans": [
    {{
      "day": 1,
      "schedules": [
        {{
          "time_slot": "오전/오후/저녁",
          "activity_type": "Spot / Meal / Cafe / Accommodation",
          "tags": ["해당 스팟에 어울리는 감성/특성 태그"],
          "location_name": "",
          "reason": "이 장소를 추천하는 1줄 이유"
        }}
      ]
    }}
  ]
}}
```
"""
```

## 2. 주요 코드 캡처 (AI API 연동 및 하이브리드 추천 엔진)
프롬프트를 GMS(SSAFY 전용 우회 API)로 전송하고 결과를 파싱하는 핵심 통신 로직입니다. 모델은 최신 `gemini-3.5-flash`를 적용했습니다.

```python
import os
import json
import requests
from recommendations.models import AICache

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
        region=region, travel_date=travel_date, duration_days=duration_days,
        departure_time=departure_time, transportation=transportation, query=query
    )

    gms_key = os.getenv("GMS_API_KEY")
    url = "https://gms.ssafy.io/gmsapi/generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash:generateContent"
    headers = { "Content-Type": "application/json", "x-goog-api-key": gms_key }
    payload = {
        "contents": [{ "parts": [{ "text": prompt }] }],
        "generationConfig": { "temperature": 0.1 } # JSON 포맷의 안정성을 위해 낮은 temperature 적용
    }

    try:
        res = requests.post(url, headers=headers, json=payload, timeout=15)
        res.raise_for_status()
        raw_text = res.json()["candidates"][0]["content"]["parts"][0]["text"].strip()

        # 마크다운 텍스트에서 JSON 추출 및 파싱
        if raw_text.startswith("```json"):
            raw_text = raw_text[7:-3].strip()

        data = json.loads(raw_text)

        if "daily_plans" in data:
            AICache.objects.get_or_create(query_key=cache_key, defaults={"parsed_result": data})

        return data

    except Exception as e:
        print(f"Gemini API Error: {e}")
        return _fallback_parse(region, travel_date, query)
```
