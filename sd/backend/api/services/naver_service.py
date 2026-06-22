import os
import requests
import re
from datetime import datetime, timedelta
from api.models import TemporaryEvent

def extract_dates_from_text(text: str, default_start: datetime.date):
    """
    텍스트에서 날짜(예: 2026.06.25 또는 06.25 ~ 07.10)를 정규표현식으로 추출합니다.
    """
    # MM.DD 또는 MM/DD 형식 추출
    pattern = r'(?:20\d{2}[-/.])?(\d{1,2})[-/.](\d{1,2})'
    matches = re.findall(pattern, text)
    
    start_date = default_start
    end_date = start_date + timedelta(days=14) # 기본 2주 유지
    
    if len(matches) >= 1:
        try:
            m1, d1 = int(matches[0][0]), int(matches[0][1])
            start_date = datetime(default_start.year, m1, d1).date()
            if start_date < default_start - timedelta(days=30):
                # 연도가 넘어간 경우 (예: 작년 날짜)
                start_date = datetime(default_start.year + 1, m1, d1).date()
                
            if len(matches) >= 2:
                m2, d2 = int(matches[-1][0]), int(matches[-1][1])
                end_date = datetime(default_start.year, m2, d2).date()
                if end_date < start_date:
                    end_date = datetime(default_start.year + 1, m2, d2).date()
            else:
                end_date = start_date + timedelta(days=14)
        except:
            pass
            
    return start_date, end_date

def fetch_and_save_naver_events(region: str, category: str):
    """
    네이버 검색 API를 통해 일시적 행사(팝업, 전시회 등)를 검색하고,
    설명란에서 날짜를 정규표현식으로 파싱하여 DB에 저장합니다. (AI 호출 제거로 속도 및 한도 최적화)
    """
    client_id = os.getenv("NAVER_CLIENT_ID")
    client_secret = os.getenv("NAVER_CLIENT_SECRET")
    
    if not client_id or not client_secret:
        raise ValueError("NAVER API credentials are not set")

    headers = {
        "X-Naver-Client-Id": client_id,
        "X-Naver-Client-Secret": client_secret
    }
    
    query = f"{region} {category}"
    url = f"https://openapi.naver.com/v1/search/local.json?query={query}&display=5"
    
    res = requests.get(url, headers=headers)
    if res.status_code != 200:
        return []

    data = res.json()
    items = data.get("items", [])
    
    if not items:
        return []

    saved_events = []
    today = datetime.now().date()
    
    # DB 저장
    for item in items:
        title = item.get("title", "").replace("<b>", "").replace("</b>", "")
        description = item.get("description", "")
        address = item.get("address", "")
        link = item.get("link", "")
        
        # 정규표현식으로 제목과 설명에서 날짜 파싱
        start_date, end_date = extract_dates_from_text(title + " " + description, today)
                
        # 중복 방지를 위해 title과 region 기준으로 조회
        event, created = TemporaryEvent.objects.get_or_create(
            name=title,
            region=region,
            defaults={
                "category": category,
                "address": address,
                "start_date": start_date,
                "end_date": end_date,
                "link": link
            }
        )
        saved_events.append(event)

    return saved_events
