import os
import requests
from recommendations.models import FixedPlace, Tag


def fetch_and_save_kakao_places(region: str, category: str, tags: list) -> list:
    """
    카카오 로컬 API로 장소를 검색하고 FixedPlace DB에 저장/업데이트합니다.
    Kakao API 응답에서 x(경도)/y(위도) 좌표를 함께 저장합니다.
    """
    kakao_key = os.getenv("KAKAO_REST_KEY")
    if not kakao_key:
        print("KAKAO_REST_API_KEY is not set")
        return []

    headers = {"Authorization": f"KakaoAK {kakao_key}"}
    
    query_parts = [region]
    # '관광명소'라는 단어는 너무 포괄적이라 카카오 검색을 망칠 수 있음 (특히 특정 장소 검색 시)
    if category and category != '관광명소':
        query_parts.append(category)
    if tags:
        query_parts.extend(tags)
        
    query = " ".join(query_parts)
    url = f"https://dapi.kakao.com/v2/local/search/keyword.json?query={query}&size=10"

    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            print(f"Kakao API error: {response.status_code}")
            return []
    except Exception as e:
        print(f"Kakao API request failed: {e}")
        return []

    documents = response.json().get("documents", [])
    saved_places = []

    for doc in documents:
        place_id = doc["id"]

        try:
            place = FixedPlace.objects.get(id=place_id)
            # 이미 있으면 태그만 업데이트
            _update_tags(place, tags)
            saved_places.append(place)
            continue
        except FixedPlace.DoesNotExist:
            pass

        try:
            place = FixedPlace.objects.create(
                id=place_id,
                name=doc["place_name"],
                address=doc["address_name"],
                region=region,
                category=category,
                latitude=float(doc.get("y", 0)),    # 위도
                longitude=float(doc.get("x", 0)),   # 경도
                image_url=None,
                place_url=doc["place_url"]
            )
            _update_tags(place, tags)
            saved_places.append(place)
            try:
                _append_to_unified_dataset(doc)
            except Exception as e:
                print(f"Error appending to unified_dataset: {e}")
        except Exception as e:
            print(f"Error saving FixedPlace {place_id}: {e}")
            continue

    return saved_places

def _append_to_unified_dataset(doc):
    import json, os
    from django.conf import settings
    
    file_path = os.path.join(settings.BASE_DIR.parent, 'data', 'unified_dataset.json')
    if not os.path.exists(file_path):
        return
        
    new_item = {
        "id": doc["id"],
        "source": "kakao",
        "title": doc["place_name"],
        "category": doc.get("category_name", ""),
        "address": doc["address_name"],
        "telephone": doc.get("phone", ""),
        "location": {
            "lat": doc.get("y", "0"),
            "lng": doc.get("x", "0")
        },
        "url": doc.get("place_url", ""),
        "original_data": {
            "original_title": doc["place_name"],
            "original_source": "user_search"
        },
        "image_url": ""
    }
    
    with open(file_path, 'rb+') as f:
        # 끝에서 100바이트 정도만 읽어서 마지막 ']'를 찾습니다. O(1) 시간 복잡도.
        f.seek(0, os.SEEK_END)
        file_size = f.tell()
        chunk_size = min(file_size, 100)
        f.seek(-chunk_size, os.SEEK_END)
        tail = f.read()
        
        idx = tail.rfind(b']')
        if idx != -1:
            f.seek(-chunk_size + idx, os.SEEK_END)
            new_data_str = ",\n  " + json.dumps(new_item, ensure_ascii=False) + "\n]"
            f.write(new_data_str.encode('utf-8'))



def _update_tags(place: FixedPlace, tags_list: list):
    """FixedPlace에 태그 추가"""
    for t in tags_list:
        if not t:
            continue
        tag_obj, _ = Tag.objects.get_or_create(name=t)
        place.tags.add(tag_obj)
