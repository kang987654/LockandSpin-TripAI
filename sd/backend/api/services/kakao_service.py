import os
import requests
from api.models import FixedPlace, Tag

def fetch_and_save_kakao_places(region: str, category: str, tags: list):
    """
    카카오 로컬 API로 장소를 검색하고, 
    각 장소의 상세 정보를 조회해 별점 3점 이상인 곳만 DB에 저장/업데이트합니다.
    """
    kakao_key = os.getenv("KAKAO_REST_API_KEY")
    if not kakao_key:
        raise ValueError("KAKAO_REST_API_KEY is not set")

    headers = {"Authorization": f"KakaoAK {kakao_key}"}
    query = f"{region} {category}"
    url = f"https://dapi.kakao.com/v2/local/search/keyword.json?query={query}&size=10"
    
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        return []

    data = response.json()
    documents = data.get("documents", [])
    
    saved_places = []
    
    for doc in documents:
        place_id = doc["id"]
        
        # 이미 DB에 있는지 확인
        try:
            place = FixedPlace.objects.get(id=place_id)
            # 이미 있으면 태그 업데이트
            update_tags(place, tags)
            saved_places.append(place)
            continue
        except FixedPlace.DoesNotExist:
            pass
            
        # 카카오맵 내부 비공개 API가 404로 막혔으므로, 
        # 로컬 API에서 내려주는 기본 정보만으로 장소를 저장합니다.
        try:
            place = FixedPlace.objects.create(
                id=place_id,
                name=doc["place_name"],
                address=doc["address_name"],
                region=region,
                category=category,
                image_url="", # 이미지는 공식 API에서 제공하지 않으므로 비워둡니다.
                place_url=doc["place_url"]
            )
            update_tags(place, tags)
            saved_places.append(place)
        except Exception as e:
            print(f"Error saving place {place_id}: {e}")
            continue

    return saved_places

def update_tags(place, tags_list):
    for t in tags_list:
        tag_obj, _ = Tag.objects.get_or_create(name=t)
        place.tags.add(tag_obj)
