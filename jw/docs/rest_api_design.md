# REST API 설계서 (REST API Design)

이 문서는 **"Lock & Spin"** 서비스의 프론트엔드(Vue)와 백엔드(Django REST Framework) 간 통신 및 실시간 협업(소셜 스핀)을 위한 REST API & WebSocket 규격을 정의합니다.

---

## 1. API Endpoint 목록 요약

| 기능 분류 | Method | URI Path | 설명 |
| :--- | :--- | :--- | :--- |
| **인증** | `POST` | `/api/auth/register/` | 회원 가입 |
| | `POST` | `/api/auth/login/` | 로그인 (토큰 발급) |
| **사용자 설정** | `GET` | `/api/user/preference/` | 사용자 선호 및 비토(기피) 목록 조회 |
| | `PUT` | `/api/user/preference/` | 사용자 선호 및 비토(기피) 목록 수정 |
| **여행 코스** | `POST` | `/api/courses/` | 조건 설정을 기반으로 한 코스 초기 생성 (최초 AI 추천) |
| | `GET` | `/api/courses/` | 사용자의 저장된 여행 코스 목록 조회 |
| | `GET` | `/api/courses/<course_id>/` | 특정 여행 코스 상세 (슬롯 목록) 조회 |
| | `PUT` | `/api/courses/<course_id>/` | 편집 완료된 최종 여행 코스 저장 |
| | `DELETE` | `/api/courses/<course_id>/` | 여행 코스 삭제 |
| **공동 편집 멤버**| `GET` | `/api/courses/<course_id>/members/` | **[소셜 스핀]** 해당 코스에 초대된 참여 멤버 목록 조회 |
| | `POST` | `/api/courses/<course_id>/members/` | **[소셜 스핀]** 새로운 멤버 초대 (이메일 기반) |
| | `DELETE` | `/api/courses/<course_id>/members/<user_id>/` | **[소셜 스핀]** 참여 멤버 추방 또는 내보내기 |
| **추천 엔진** | `POST` | `/api/courses/<course_id>/spin/` | Lock 상태가 반영된 미잠금 슬롯 재추천 (Re-spin) |

---

## 2. 상세 API 명세

### 2.1. 사용자 선호 설정 조회/수정 (`/api/user/preference/`)

* **GET /api/user/preference/**
  * **Header**: `Authorization: Bearer <token>`
  * **Response (200 OK)**:
    ```json
    {
      "preferred_themes": ["healing", "activity"],
      "preferred_pace": "medium",
      "veto_categories": ["museum", "shopping"]
    }
    ```

* **PUT /api/user/preference/**
  * **Request Body**:
    ```json
    {
      "preferred_themes": ["healing", "nature", "activity"],
      "preferred_pace": "slow",
      "veto_categories": ["museum"]
    }
    ```
  * **Response (200 OK)**: (수정 완료된 데이터 반환)

---

### 2.2. 코스 초기 생성 및 조회

* **POST /api/courses/**
  * **Request Body**:
    ```json
    {
      "title": "강릉 가족 여행",
      "destination": "강릉",
      "start_date": "2026-06-01",
      "duration_days": 2
    }
    ```
  * **Response (201 Created)**:
    * `latitude` 및 `longitude` 정보를 응답에 포함시켜 프론트엔드가 지도 컴포넌트(Kakao Map 등) 상에 핀을 즉시 매핑할 수 있도록 함.
    ```json
    {
      "course_id": 42,
      "title": "강릉 가족 여행",
      "destination": "강릉",
      "start_date": "2026-06-01",
      "duration_days": 2,
      "slots": [
        {
          "day_number": 1,
          "sequence": 1,
          "is_locked": false,
          "place": {
            "id": 101,
            "name": "경포해변",
            "category": "spot",
            "themes": ["nature", "healing"],
            "latitude": 37.7981,
            "longitude": 128.9161,
            "address": "강원특별자치도 강릉시 안현동 산1"
          }
        },
        {
          "day_number": 1,
          "sequence": 2,
          "is_locked": false,
          "place": {
            "id": 102,
            "name": "초당토부두부",
            "category": "restaurant",
            "themes": ["food"],
            "latitude": 37.7905,
            "longitude": 128.9145,
            "address": "강원특별자치도 강릉시 초당순두부길 77"
          }
        }
      ]
    }
    ```

---

### 2.3. 공동 편집 멤버 관리 API (소셜 스핀 확장)

* **GET /api/courses/<course_id>/members/**
  * **Response (200 OK)**:
    ```json
    [
      {
        "user_id": 1,
        "username": "creator_user",
        "email": "owner@example.com",
        "role": "owner"
      },
      {
        "user_id": 5,
        "username": "friend_user",
        "email": "friend@example.com",
        "role": "editor"
      }
    ]
    ```

* **POST /api/courses/<course_id>/members/**
  * **Request Body**:
    ```json
    {
      "email": "friend@example.com",
      "role": "editor"
    }
    ```
  * **Response (201 Created)**: (초대 성공 메시지 및 등록된 멤버 정보 반환)

---

### 2.4. 슬롯 재조합 (Re-spin) API (`POST /api/courses/<course_id>/spin/`)
사용자가 특정 슬롯을 고정하고 'Re-spin' 버튼을 눌렀을 때 호출됩니다. (동선 최적화 알고리즘 기반으로 미잠금 장소가 교체됩니다.)

* **Request Body**:
  ```json
  {
    "slots": [
      {
        "day_number": 1,
        "sequence": 1,
        "is_locked": true,
        "place_id": 101
      },
      {
        "day_number": 1,
        "sequence": 2,
        "is_locked": false,
        "place_id": 102
      }
    ]
  }
  ```
* **Response (200 OK)**:
  ```json
  {
    "course_id": 42,
    "slots": [
      {
        "day_number": 1,
        "sequence": 1,
        "is_locked": true,
        "place": {
          "id": 101,
          "name": "경포해변",
          "category": "spot",
          "themes": ["nature", "healing"],
          "latitude": 37.7981,
          "longitude": 128.9161,
          "address": "강원특별자치도 강릉시 안현동 산1"
        }
      },
      {
        "day_number": 1,
        "sequence": 2,
        "is_locked": false,
        "place": {
          "id": 105,
          "name": "강릉짬뽕갈비",
          "category": "restaurant",
          "themes": ["food"],
          "latitude": 37.7912,
          "longitude": 128.9150,
          "address": "강원특별자치도 강릉시 초당순두부길 116"
        }
      }
    ]
  }
  ```

---

## 3. 웹소켓 실시간 브로드캐스트 (WebSocket Events)

소셜 스핀 기능을 위해 방(Room) 단위의 실시간 상태 동기화 프로토콜을 사용합니다.
* **연결 엔드포인트**: `ws://<domain>/ws/courses/<course_id>/`

### 3.1. 클라이언트 $\rightarrow$ 서버 이벤트 (슬롯 잠금 토글)
한 동행자가 특정 슬롯을 클릭해 Lock 상태를 토글하면 다른 동행자의 화면에도 실시간으로 반영됩니다.
```json
{
  "event": "toggle_lock",
  "data": {
    "day_number": 1,
    "sequence": 2,
    "is_locked": true
  }
}
```

### 3.2. 서버 $\rightarrow$ 클라이언트 브로드캐스트 (상태 동기화)
그룹 인원 중 한 명에 의해 발생한 코스 변경 사항(Lock 변경, Re-spin 완료 등)을 모든 참여자 화면에 즉시 브로드캐스트합니다.
```json
{
  "event": "course_updated",
  "data": {
    "slots": [
      { "day_number": 1, "sequence": 1, "is_locked": true, "place_id": 101 },
      { "day_number": 1, "sequence": 2, "is_locked": true, "place_id": 102 }
    ]
  }
}
```

---

## 4. 에러 처리 규격

* **400 Bad Request**: 필수 필드 누락 또는 요청 포맷 에러
* **401 Unauthorized**: 자격 증명 누락
* **403 Forbidden**: 코스 편집 권한이 없는 참여자가 수정 시도
