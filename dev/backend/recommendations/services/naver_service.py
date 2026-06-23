import os
import re
import requests
from datetime import datetime, timedelta
from recommendations.models import TemporaryEvent


def extract_dates_from_text(text: str, default_start):
    """
    텍스트에서 날짜(예: 2026.06.25 또는 06.25 ~ 07.10)를 정규표현식으로 추출합니다.
    """
    pattern = r'(?:20\d{2}[-/.])?(\\d{1,2})[-/.](\\d{1,2})'
    matches = re.findall(pattern, text)

    start_date = default_start
    end_date = start_date + timedelta(days=14)  # 기본 2주

    if len(matches) >= 1:
        try:
            m1, d1 = int(matches[0][0]), int(matches[0][1])
            start_date = datetime(default_start.year, m1, d1).date()
            if start_date < default_start - timedelta(days=30):
                start_date = datetime(default_start.year + 1, m1, d1).date()

            if len(matches) >= 2:
                m2, d2 = int(matches[-1][0]), int(matches[-1][1])
                end_date = datetime(default_start.year, m2, d2).date()
                if end_date < start_date:
                    end_date = datetime(default_start.year + 1, m2, d2).date()
            else:
                end_date = start_date + timedelta(days=14)
        except Exception:
            pass

    return start_date, end_date


def fetch_and_save_naver_events(region: str, category: str) -> list:
    """
    네이버 검색 API로 일시적 행사(팝업, 전시회 등)를 검색하고 DB에 저장합니다.
    """
    client_id = os.getenv("NAVER_CLIENT_ID")
    client_secret = os.getenv("NAVER_CLIENT_SECRET")

    if not client_id or not client_secret:
        print("NAVER API credentials are not set")
        return []

    headers = {
        "X-Naver-Client-Id": client_id,
        "X-Naver-Client-Secret": client_secret
    }

    query = f"{region} {category}"
    url = f"https://openapi.naver.com/v1/search/local.json?query={query}&display=5"

    try:
        res = requests.get(url, headers=headers, timeout=10)
        if res.status_code != 200:
            print(f"Naver API error: {res.status_code}")
            return []
    except Exception as e:
        print(f"Naver API request failed: {e}")
        return []

    items = res.json().get("items", [])
    if not items:
        return []

    saved_events = []
    today = datetime.now().date()

    for item in items:
        title = item.get("title", "").replace("<b>", "").replace("</b>", "")
        description = item.get("description", "")
        address = item.get("address", "")
        link = item.get("link", "")

        start_date, end_date = extract_dates_from_text(title + " " + description, today)

        event, _ = TemporaryEvent.objects.get_or_create(
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
