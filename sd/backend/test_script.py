import os
import sys
import django

# Setup Django
sys.path.append('c:/Users/SSAFY/Desktop/search api/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from api.services.kakao_service import fetch_and_save_kakao_places

places = fetch_and_save_kakao_places("잠실", "카페", ["실내데이트"])
print("Found Kakao places:", len(places))
for p in places:
    print(p.name, p.category, p.region)

from api.services.ai_service import parse_user_request
res = parse_user_request("잠실", "2026-06-23", "실내데이트")
print("AI parsing result:", res)
