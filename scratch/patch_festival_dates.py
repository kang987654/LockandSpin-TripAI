import json
import asyncio
import aiohttp
import ssl
import time

api_key = '1a49cb069a5eccc02e77d28ddec5bdae1dac701866ad448eabd8b1626f49c77d'
unified_file = 'data/unified_dataset.json'

with open(unified_file, 'r', encoding='utf-8') as f:
    unified_data = json.load(f)

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

async def fetch_dates(session, item, sem):
    if item.get('source') != 'tour_api_festival':
        return False
        
    content_id = item.get('id') # unified format uses contentid as 'id' for festivals
    if not content_id:
        return False

    url = f'http://apis.data.go.kr/B551011/KorService2/detailIntro2?serviceKey={api_key}&numOfRows=1&pageNo=1&MobileOS=ETC&MobileApp=AppTest&contentId={content_id}&contentTypeId=15&_type=json'
    
    async with sem:
        for _ in range(3):
            try:
                async with session.get(url, timeout=10) as response: # Note: disabled SSL verify in session setup
                    if response.status == 200:
                        data = await response.json()
                        items = data.get('response', {}).get('body', {}).get('items', '')
                        if items and isinstance(items, dict):
                            item_list = items.get('item', [])
                            if item_list:
                                intro = item_list[0]
                                start_date = intro.get('eventstartdate', '')
                                end_date = intro.get('eventenddate', '')
                                
                                # Format dates from YYYYMMDD to YYYY-MM-DD
                                if len(start_date) == 8:
                                    start_date = f"{start_date[:4]}-{start_date[4:6]}-{start_date[6:]}"
                                if len(end_date) == 8:
                                    end_date = f"{end_date[:4]}-{end_date[4:6]}-{end_date[6:]}"
                                    
                                item['start_date'] = start_date
                                item['end_date'] = end_date
                                return True
            except Exception as e:
                pass
            await asyncio.sleep(0.5)
    return False

async def main():
    festivals = [item for item in unified_data if item.get('source') == 'tour_api_festival']
    print(f"Total festivals to update: {len(festivals)}")
    
    sem = asyncio.Semaphore(20)
    conn = aiohttp.TCPConnector(ssl=ctx)
    success_count = 0
    
    async with aiohttp.ClientSession(connector=conn) as session:
        tasks = [fetch_dates(session, item, sem) for item in festivals]
        
        completed = 0
        total = len(tasks)
        for f in asyncio.as_completed(tasks):
            res = await f
            completed += 1
            if res:
                success_count += 1
                
            if completed % 100 == 0:
                print(f"Processed {completed}/{total} ... Success: {success_count}")

    with open(unified_file, 'w', encoding='utf-8') as f:
        json.dump(unified_data, f, ensure_ascii=False, indent=2)
        
    print(f"Updated dates for {success_count} festival items.")

if __name__ == '__main__':
    asyncio.run(main())
