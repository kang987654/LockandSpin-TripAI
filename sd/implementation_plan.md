# AI 기반 여행 및 데이트 코스 추천 API 구현 계획서

요청해주신 피드백을 반영하여 계획서를 업데이트했습니다. 프론트엔드는 **Vue.js**, 백엔드는 **Django**로 기술 스택을 변경하여 안정적이고 체계적인 풀스택 구조를 구성합니다. 데이터의 성격(고정적 장소 vs 일시적 행사)에 따라 수집 방식은 다르지만, 모든 데이터를 자체 DB화하여 효율을 극대화하는 Dual-track 구조는 동일하게 유지됩니다.

## 시스템 개요 및 타당성 검토 (Feasibility)
1. **자연어 요구사항 분석 (Gemini API)**: 사용자의 자유 텍스트 입력을 기반으로 지역, 카테고리, 특성을 추출합니다. 이때 요청이 **고정적 장소**인지 **일시적 행사**인지, 그리고 **사용자의 여행 날짜**까지 추출하도록 프롬프트를 구성합니다.
2. **트랙 A: 고정적 장소 (음식점, 카페, 숙소, 공방, 액티비티 등)**
   - 카카오 로컬 API로 검색 후, 웹페이지를 크롤링하여 **별점이 3점 이상인 곳만 DB에 저장**합니다. (별점 수치 자체는 미저장)
3. **트랙 B: 일시적 활동 (팝업, 전시회, 행사, 공연 등)**
   - 네이버 검색 API를 통해 행사를 찾습니다. 
   - **이벤트 기간(시작일~종료일)을 파싱하여 DB에 함께 저장**합니다.
   - 이후 추천 시, DB 내 이벤트 기간이 사용자의 '여행 날짜'를 포함하는 경우에만 즉시 추천에 활용합니다.

---

## 확정된 기술 스택

- **프론트엔드**: Vue.js (Vite 기반, Vue 3, Composition API) + TailwindCSS (깔끔하고 동적인 UI)
- **백엔드**: Python + Django (Django REST Framework 활용)
- **데이터베이스**: SQLite + Django ORM (로컬 파일 기반으로 쉽게 시작하고 데이터 누적이 가능)
- **크롤링 도구**: `requests` + `BeautifulSoup` (장소 별점 필터링용)

---

## Proposed Changes

프론트엔드(Vue.js)와 백엔드(Django)를 포함한 전체 풀스택 구조로 변경됩니다.

### 1. 환경 설정 및 파일 구조
#### [NEW] `frontend/`
- Vite + Vue 3 기반의 사용자 UI (채팅창 형태의 추천 입력 인터페이스, 장소 및 행사 결과 리스트, 지도/이미지 위젯 등)
#### [NEW] `backend/`
- Django 프로젝트 및 앱 코드가 위치할 폴더
#### [NEW] `backend/.env`
- Gemini, Kakao, Naver API 키 등 환경 변수 보관
#### [NEW] `backend/requirements.txt`
- `django`, `djangorestframework`, `google-genai` (또는 `google-generativeai`), `requests`, `beautifulsoup4`, `python-dotenv` 등 패키지 목록

### 2. 데이터베이스 스키마 및 고속 검색 아키텍처 (`backend/api/models.py`)
빠른 검색과 추천을 위해 **DB 인덱싱(Indexing)**과 **태그(Tag) 정규화**를 적용합니다. 단순히 텍스트를 검색하는 것보다 검색 속도를 수십 배 이상 끌어올릴 수 있습니다.

#### [NEW] `Tag` 모델 (특성/분위기 키워드)
- '조용한', '분위기있는', '가성비' 등의 키워드를 독립된 테이블로 관리하여 초고속 매칭 지원.

#### [NEW] `FixedPlace` 모델 (트랙 A)
- 카카오 API로 수집한 **별점 3점 이상**의 고정 장소 저장
- **필드 구성**: ID(카카오 장소ID, PK), 이름, 주소, 이미지 URL, 카카오맵 URL
- **검색 최적화 (Index)**:
  - `region` (지역명 - 예: '홍대', '강남'): `db_index=True` 적용
  - `category` (분류 - 예: '카페', '음식점'): `db_index=True` 적용
- **다대다(M2M) 관계**: `tags` 필드를 통해 `Tag` 모델과 연결. (예: 홍대(인덱스) + 카페(인덱스) + '조용한'(태그 조인) 조건으로 밀리초 단위 검색 가능)

#### [NEW] `TemporaryEvent` 모델 (트랙 B)
- 팝업, 전시회 등 일시적 행사 저장
- **필드 구성**: ID(PK), 이름, 주소, 이미지 URL, 네이버 링크 URL
- **검색 최적화 (Index)**:
  - `region`, `category`: `db_index=True` 적용
  - `start_date`, `end_date`: `db_index=True` 적용 (사용자의 여행 날짜가 이 기간 안에 포함되는지 즉시 필터링)

### 3. 백엔드 코어 비즈니스 로직 (`backend/api/services/`)
#### [NEW] `ai_service.py`
- 요구사항을 '트랙 A'와 '트랙 B'로 분류하고, 사용자의 **여행 날짜**까지 파싱.
#### [NEW] `kakao_service.py`
- 카카오 API 검색 및 `place_url` 크롤링(별점 3점 이상 필터링).
#### [NEW] `naver_service.py`
- 트랙 B 전용. 네이버 검색 API 결과를 기반으로 행사 정보와 **진행 기간(Dates)**을 파싱하는 로직.
#### [NEW] `recommendation_service.py`
- 트랙 A, B 로직을 분기하고 통합. DB에서 여행 날짜와 이벤트 기간이 겹치는지(`start_date <= travel_date <= end_date`) 조건 검색.

### 4. API 엔드포인트 (`backend/api/views.py` & `urls.py`)
#### [NEW] `POST /api/recommend/` 엔드포인트 구현
- Django REST Framework(DRF) 기반으로 클라이언트 요청을 받아 로직을 처리하고 JSON 형태로 반환합니다.

---

## Verification Plan

### Automated Tests & Manual Verification
1. **Django 및 Vue.js 연동 테스트**: 프론트엔드 화면에서 텍스트 입력 시 Django 백엔드를 거쳐 응답이 돌아오는지 확인.
2. **여행 날짜 및 트랙 분류 검증**: "이번주 토요일에 강남 팝업스토어" 입력 시 트랙 B로 빠지며 '이번주 토요일'의 실제 날짜값이 계산되는지 Python 로직 단에서 검증.
3. **DB 저장 및 필터링 검증**: 
   - 카카오맵 크롤러가 3점 이상인 곳만 DB에 남기는지 확인.
   - 네이버 검색으로 파싱된 행사 기간과 여행 날짜 조건이 맞을 때만 추천에 포함되는지 확인.

---

Vue.js와 Django 기반으로 재작성된 계획서를 확인해 보시고, 더 추가하거나 수정하고 싶으신 부분이 있다면 언제든 말씀해 주세요! 모두 괜찮으시다면 이대로 실행에 옮기겠습니다.
