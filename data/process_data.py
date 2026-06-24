import os
import json
import asyncio
import aiohttp
import time

API_URL = "https://dapi.kakao.com/v2/local/search/keyword.json"

def get_api_key():
    env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
    with open(env_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.startswith('KAKAO_REST_KEY'):
                return line.split('=')[1].strip().strip("'").strip('"')
    return None

API_KEY = get_api_key()
HEADERS = {"Authorization": f"KakaoAK {API_KEY}"}

async def fetch_kakao_data(session, item, sem):
    async with sem:
        title = item.get('title', '')
        # add address hint if available for better accuracy
        addr_hint = item.get('roadAddress') or item.get('address') or item.get('addr1') or ''
        # We search with title
        query = title
        if 'naver_data' in item.get('_source_file', ''):
            # Naver data might have better region keyword
            region = item.get('region_keyword', '')
            if region: query = f"{region} {title}"
            
        params = {"query": query, "size": 1}
        
        for _ in range(3): # retry logic
            try:
                async with session.get(API_URL, headers=HEADERS, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        documents = data.get('documents', [])
                        if documents:
                            doc = documents[0]
                            return {
                                "id": doc.get('id'),
                                "source": "kakao",
                                "title": doc.get('place_name'),
                                "category": doc.get('category_name'),
                                "address": doc.get('road_address_name') or doc.get('address_name'),
                                "telephone": doc.get('phone'),
                                "location": {
                                    "lat": doc.get('y'),
                                    "lng": doc.get('x')
                                },
                                "url": doc.get('place_url'),
                                "original_data": {
                                    "original_title": title,
                                    "original_source": item.get('_source_file')
                                }
                            }
                    elif response.status == 429:
                        await asyncio.sleep(1)
                        continue
            except Exception:
                pass
            await asyncio.sleep(0.5)
            
        # fallback to original if API fails or no result
        return {
            "id": item.get('contentid') or f"generated_{hash(title)}",
            "source": "fallback",
            "title": title,
            "category": item.get('category') or item.get('cat3'),
            "address": addr_hint,
            "telephone": item.get('telephone') or item.get('tel'),
            "location": {
                "lat": item.get('mapy'),
                "lng": item.get('mapx')
            },
            "url": item.get('link') or item.get('firstimage'),
            "original_data": {
                "original_source": item.get('_source_file')
            }
        }

async def process_all_data():
    dataset_dir = os.path.join(os.path.dirname(__file__), '..', 'dataset')
    output_file = os.path.join(os.path.dirname(__file__), 'unified_dataset.json')
    
    all_items = []
    fest_items = []
    
    print("Reading files...")
    for f in os.listdir(dataset_dir):
        if not f.endswith('.json'): continue
        path = os.path.join(dataset_dir, f)
        with open(path, 'r', encoding='utf-8') as file:
            data = json.load(file)
            for item in data:
                item['_source_file'] = f
                if '축제공연행사' in f:
                    # Festival mapping directly
                    fest_items.append({
                        "id": item.get('contentid'),
                        "source": "tour_api_festival",
                        "title": item.get('title'),
                        "category": item.get('cat1', '') + " " + item.get('cat2', '') + " " + item.get('cat3', ''),
                        "address": item.get('addr1'),
                        "telephone": item.get('tel'),
                        "location": {
                            "lat": item.get('mapy'),
                            "lng": item.get('mapx')
                        },
                        "url": item.get('firstimage'),
                        "original_data": {
                            "original_source": f
                        }
                    })
                else:
                    all_items.append(item)
                    
    print(f"Total Kakao API items to process: {len(all_items)}")
    print(f"Total Festival items: {len(fest_items)}")
    
    sem = asyncio.Semaphore(50) # 50 concurrent
    
    results = []
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_kakao_data(session, item, sem) for item in all_items]
        
        total = len(tasks)
        completed = 0
        start_time = time.time()
        
        for f in asyncio.as_completed(tasks):
            res = await f
            results.append(res)
            completed += 1
            if completed % 1000 == 0:
                elapsed = time.time() - start_time
                rate = completed / elapsed
                print(f"Processed {completed}/{total} ... ({rate:.2f} req/s)")

    # Combine with festivals
    final_data = results + fest_items
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(final_data, f, ensure_ascii=False, indent=2)
        
    print(f"Successfully saved {len(final_data)} items to {output_file}")

if __name__ == "__main__":
    if not API_KEY:
        print("API Key not found!")
    else:
        asyncio.run(process_all_data())
