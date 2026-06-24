import os
import requests
import json
import urllib.parse
import dotenv
from django.core.management.base import BaseCommand
from django.conf import settings
from places.models import Place

# Load environment variables from .env
dotenv.load_dotenv(os.path.join(os.path.dirname(settings.BASE_DIR), '.env'))

class Command(BaseCommand):
    help = 'Collects and seeds real place data using Korea Tourism Organization (TourAPI 4.0) and Kakao Local API'

    def add_arguments(self, parser):
        parser.add_argument('--tourapi-key', type=str, help='TourAPI Service Key')
        parser.add_argument('--kakao-key', type=str, help='Kakao REST API Key')
        parser.add_argument('--area-code', type=int, default=1, help='Area code for TourAPI (1: Seoul, 32: Gangwon)')
        parser.add_argument('--limit', type=int, default=50, help='Max number of items to fetch per content type')

    def handle(self, *args, **options):
        # Load keys from parameters, fall back to .env environment variables
        tourapi_key = options.get('tourapi_key') or os.environ.get('TOUR_API_KEY')
        kakao_key = options.get('kakao_key') or os.environ.get('KAKAO_REST_API_KEY')
        area_code = options.get('area_code')
        limit = options.get('limit')

        if not tourapi_key:
            self.stdout.write(self.style.ERROR('TourAPI Key가 누락되었습니다. .env를 확인하시거나 --tourapi-key 옵션을 지정해주세요.'))
            return

        area_name = "서울" if area_code == 1 else "해당 지역"
        self.stdout.write(f'{area_name} (지역코드: {area_code}) 데이터 수집을 시작합니다...')

        # Content types mapping: 12 (Spots), 14 (Culture), 28 (Reports/Activity), 39 (Food)
        content_types = {
            12: 'spot',
            14: 'spot',
            28: 'activity',
            39: 'restaurant'
        }

        fetched_count = 0

        for content_type_id, category_label in content_types.items():
            self.stdout.write(f'Content Type ID {content_type_id} ({category_label}) 수집 중...')
            
            base_url = "http://apis.data.go.kr/B551011/KorService2/areaBasedList2"
            unquoted_key = urllib.parse.unquote(tourapi_key)
            full_url = f"{base_url}?serviceKey={unquoted_key}"

            # listYN 파라미터는 KorService2에서 지원하지 않으므로 제외
            params = {
                "numOfRows": limit,
                "pageNo": 1,
                "MobileOS": "ETC",
                "MobileApp": "LockAndSpin",
                "_type": "json",
                "areaCode": area_code,
                "contentTypeId": content_type_id,
                "arrange": "A"
            }

            try:
                res = requests.get(full_url, params=params, timeout=10)
                if res.status_code != 200:
                    self.stdout.write(self.style.WARNING(f'HTTP Error {res.status_code} 발생.'))
                    continue

                response_data = res.json()
                
                # Check for portal authentication errors
                header = response_data.get('response', {}).get('header', {})
                result_code = header.get('resultCode')
                result_msg = header.get('resultMsg')
                
                if result_code != '0000':
                    self.stdout.write(self.style.WARNING(f'TourAPI 응답 에러 코드 검출: [{result_code}] {result_msg}'))
                    # Retry with raw key
                    full_url_raw = f"{base_url}?serviceKey={tourapi_key}"
                    res = requests.get(full_url_raw, params=params, timeout=10)
                    response_data = res.json()
                    header = response_data.get('response', {}).get('header', {})
                    if header.get('resultCode') != '0000':
                        self.stdout.write(self.style.ERROR(f'TourAPI 재시도 에러 코드 검출: [{header.get("resultCode")}] {header.get("resultMsg")}'))
                        continue

                body = response_data.get('response', {}).get('body', {})
                items = body.get('items', {})
                
                if not items:
                    self.stdout.write(f'수집할 데이터가 없습니다.')
                    continue

                item_list = items.get('item', [])
                if isinstance(item_list, dict):
                    item_list = [item_list]

                for item in item_list:
                    name = item.get('title')
                    address = item.get('addr1', '') + ' ' + item.get('addr2', '')
                    address = address.strip()
                    latitude_str = item.get('mapy')
                    longitude_str = item.get('mapx')
                    image_url = item.get('firstimage', '')

                    if not latitude_str or not longitude_str:
                        continue

                    latitude = float(latitude_str)
                    longitude = float(longitude_str)

                    # Sub-categorization
                    final_category = category_label
                    if category_label == 'restaurant' and any(kw in name for kw in ['카페', '커피', '찻집', '디저트']):
                        final_category = 'cafe'

                    themes = []
                    if final_category == 'spot':
                        themes.append('healing')
                        if any(kw in name for kw in ['산', '공원', '숲']):
                            themes.append('nature')
                        elif any(kw in name for kw in ['궁', '역사', '박물관']):
                            themes.append('culture')
                    elif final_category == 'restaurant':
                        themes.append('food')
                        if any(kw in name for kw in ['국밥', '한정식', '가든']):
                            themes.append('traditional')
                    elif final_category == 'cafe':
                        themes.append('coffee')
                        themes.append('healing')
                    elif final_category == 'activity':
                        themes.append('activity')
                        themes.append('fun')

                    description = f"{name}에 대한 소개 정보입니다."
                    
                    if kakao_key:
                        kakao_url = "https://dapi.kakao.com/v2/local/search/keyword.json"
                        headers = {"Authorization": f"KakaoAK {kakao_key}"}
                        kakao_params = {"query": f"서울 {name}", "size": 1}
                        try:
                            k_res = requests.get(kakao_url, headers=headers, params=kakao_params, timeout=5)
                            if k_res.status_code == 200:
                                k_data = k_res.json()
                                documents = k_data.get('documents', [])
                                if documents:
                                    doc = documents[0]
                                    place_url = doc.get('place_url')
                                    description = f"카카오 맵 정보 제공 목적지. 주소: {doc.get('road_address_name', address)} | 링크: {place_url}"
                        except Exception as e:
                            self.stdout.write(f'Kakao API 연동 중 예외 발생: {str(e)}')

                    place, created = Place.objects.update_or_create(
                        name=name,
                        defaults={
                            "category": final_category,
                            "themes": ",".join(themes),
                            "latitude": latitude,
                            "longitude": longitude,
                            "address": address,
                            "description": description,
                            "image_url": image_url
                        }
                    )
                    if created:
                        fetched_count += 1

            except Exception as e:
                self.stdout.write(self.style.ERROR(f'TourAPI 호출 중 예외 발생: {str(e)}'))

        self.stdout.write(self.style.SUCCESS(f'성공적으로 {fetched_count}개의 새로운 장소를 DB에 수집 및 업데이트하였습니다.'))
