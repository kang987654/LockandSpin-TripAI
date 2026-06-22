import os
import sys
import django

# Setup Django
sys.path.append('c:/Users/SSAFY/Desktop/search api/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

import requests

kakao_key = os.getenv("KAKAO_REST_API_KEY")
headers = {"Authorization": f"KakaoAK {kakao_key}"}
query = "잠실 카페"
url = f"https://dapi.kakao.com/v2/local/search/keyword.json?query={query}&size=10"

response = requests.get(url, headers=headers)
print("Kakao status:", response.status_code)
data = response.json()
print("Total documents:", len(data.get("documents", [])))

doc = data.get("documents", [])[0]
print("First doc:", doc)

place_id = doc["id"]
detail_url = f"https://place.map.kakao.com/main/v/{place_id}"
detail_res = requests.get(detail_url, headers={"User-Agent": "Mozilla/5.0"})
print("Detail status:", detail_res.status_code)
if detail_res.status_code == 200:
    basic_info = detail_res.json().get("basicInfo", {})
    score = basic_info.get("feedback", {}).get("scoresum", 0)
    count = basic_info.get("feedback", {}).get("scorecnt", 0)
    print("Scoresum:", score, "Scorecnt:", count)
else:
    print("Failed to fetch detail")
