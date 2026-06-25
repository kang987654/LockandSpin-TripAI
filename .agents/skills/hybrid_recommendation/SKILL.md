# 재사용 가능한 AI/웹 개발 스킬셋 (Reusable Skills)

이 문서는 본 프로젝트를 위한 핵심 로직과 디자인 패턴들을 스킬(Skill) 단위로 쪼개어 정의한 것입니다. 

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

