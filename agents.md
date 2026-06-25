# 전역 AI 에이전트 행동 지침 (Global Agent Rules)

이 파일은 프로젝트 전반에 걸쳐 AI 에이전트가 코드를 작성하거나 디버깅할 때 반드시 지켜야 할 핵심 원칙과 패턴을 정의합니다. 다른 프로젝트에 적용할 때도 동일한 품질과 안정성을 유지하기 위한 목적으로 작성되었습니다.

## 1. 아키텍처 및 기획 원칙 (Architecture & Planning)
- **하이브리드 AI 접근법 (Anti-Hallucination):** 
  AI를 이용해 데이터를 추천하거나 생성할 때, AI에게 최종 결과물(예: 실존하는 식당 이름)을 직접 찍어내도록 의존하지 마세요. AI는 의도(Intent)와 구조(Blueprint)만 기획하고, 실제 데이터는 내부 DB와 외부 검증된 API(Kakao, Naver 등)를 통해 스코어링하여 매핑해야 합니다. (Location Drifting 및 환각 현상 방지)
- **점진적 가입 유도 (Try Before You Buy UX):**
  비회원(Anonymous)도 핵심 기능을 체험해 볼 수 있도록 설계하세요. 데이터베이스와 뷰 로직에서 `user=null` 상태를 허용하고, 최종 저장(Save/Claim) 시점에 로그인을 유도하여 전환율을 높입니다.

## 2. 프론트엔드 (Vue.js) 구현 원칙
- **라우터 가드와 리다이렉트 (Router Guard & Redirects):**
  - 인증이 필요한 페이지로 비회원이 접근하여 로그인 창으로 튕겨낼 때는 반드시 원래 목적지 주소를 쿼리 파라미터(`?redirect=...`)로 보존해야 합니다.
  - 로그인 및 회원가입 뷰(`LoginView`, `RegisterView`) 간 이동 시에도 이 쿼리 파라미터가 유실되지 않도록 라우터 링크에 유지하세요.
- **UI 상태 기반 권한 제어 (UI Permission Control):**
  - 본인 소유가 아닌 데이터(예: 커뮤니티 공유 글)를 열람할 때, 수정/삭제/관리 관련 버튼은 서버 응답 여부와 무관하게 프론트엔드 단에서 아예 렌더링되지 않도록(`v-if="hasEditPermission"`) 원천 차단하세요.
- **인증 헤더 처리 (Auth Headers):**
  - 로그아웃 상태일 때 Axios 등 HTTP 클라이언트에서 `Authorization: Bearer undefined` 또는 빈 문자열을 전송하지 않도록 주의하세요. 백엔드에서 인증 형식이 잘못되었다며 401 에러를 뱉을 수 있습니다.

## 3. 백엔드 (Django REST Framework) 구현 원칙
- **이중 보안 점검 (Dual Security Checks):**
  - `ViewSet`의 `get_queryset()`을 오버라이딩하여, 요청자(request.user)가 접근 가능한 데이터만 응답하도록 1차 필터링하세요.
  - 개별 액션(`@action`)에서 `get_object()`를 사용할 때 권한이 없는 자가 타인의 데이터를 수정(Mutation)할 수 없도록 철저히 차단하세요.
- **익명 사용자 방어 (AnonymousUser Safe-guard):**
  - `request.user`의 속성(예: `veto_categories`, `profile`)에 접근할 때는 반드시 `request.user.is_authenticated`를 먼저 체크하세요. 익명 사용자의 속성 접근 시 발생하는 `AttributeError`로 인한 500 에러를 예방해야 합니다.
- **동적 스코어링 엔진 (Dynamic Scoring):**
  - 위치 기반 데이터를 추천할 때는 기존 앵커 포인트(확정된 장소 등)와의 거리, 구/동 단위의 행정구역 일치 여부를 점수화(Weight)하여 동선이 비현실적으로 튀는 현상을 막으세요.

## 4. 프롬프트 및 외부 API 연동
- **프롬프트 관리:**
  - AI API 호출 시 모델 버전(예: `gemini-3.5-flash`)과 엔드포인트 URL을 환경 변수나 설정 파일에 유연하게 분리하세요.
  - 응답 결과를 파싱할 때 `json` 스키마 형식을 엄격히 확인하고, API 장애 시 화면이 멈추지 않도록 기본 Fallback 텍스트(또는 DB 로직)를 반드시 마련하세요.
