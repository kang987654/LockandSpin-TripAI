import json
import asyncio
import aiohttp
import re
import time
import sys

sys.stdout.reconfigure(encoding='utf-8')

unified_file = 'data/unified_dataset.json'

with open(unified_file, 'r', encoding='utf-8') as f:
    unified_data = json.load(f)

# Regex to find og:image content
og_image_pattern = re.compile(r'<meta\s+(?:[^>]*?\s+)?property=[\'"]og:image[\'"]\s+content=[\'"]([^\'"]+)[\'"]', re.IGNORECASE)

async def fetch_image(session, item, sem):
    url = item.get('url')
    if not url or not url.startswith('http'):
        return False
        
    async with sem:
        for _ in range(2): # Retry once
            try:
                # Add timeout to avoid hanging
                async with session.get(url, timeout=10, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}) as response:
                    if response.status == 200:
                        html = await response.text()
                        match = og_image_pattern.search(html)
                        if match:
                            img_url = match.group(1)
                            if img_url.startswith('//'):
                                img_url = 'https:' + img_url
                            item['image_url'] = img_url
                            return True
                    elif response.status in [429, 403]:
                        # Rate limited or blocked
                        await asyncio.sleep(2)
                        continue
            except Exception:
                pass
            await asyncio.sleep(0.5)
    return False

async def main():
    items_to_scrape = [item for item in unified_data if 'image_url' not in item and item.get('url')]
    print(f"Total items to scrape: {len(items_to_scrape)}")
    
    if not items_to_scrape:
        print("No items need scraping.")
        return

    sem = asyncio.Semaphore(30) # 30 concurrent requests to balance speed and block risk
    
    success_count = 0
    total = len(items_to_scrape)
    start_time = time.time()
    
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_image(session, item, sem) for item in items_to_scrape]
        
        completed = 0
        for f in asyncio.as_completed(tasks):
            result = await f
            completed += 1
            if result:
                success_count += 1
            
            if completed % 500 == 0:
                elapsed = time.time() - start_time
                rate = completed / elapsed
                print(f"Scraped {completed}/{total} ... Success: {success_count} ({rate:.2f} req/s)")
                # Save intermediate progress every 5000
                if completed % 5000 == 0:
                    with open(unified_file, 'w', encoding='utf-8') as f_out:
                        json.dump(unified_data, f_out, ensure_ascii=False, indent=2)

    with open(unified_file, 'w', encoding='utf-8') as f:
        json.dump(unified_data, f, ensure_ascii=False, indent=2)
        
    print(f"\nScraping complete!")
    print(f"Successfully found images for {success_count} items.")

if __name__ == '__main__':
    asyncio.run(main())
