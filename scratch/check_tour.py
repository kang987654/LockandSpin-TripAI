import json
from collections import Counter
import random
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('data/unified_dataset.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

tour_cats = Counter()
tour_sources = Counter()
samples = []
fallback_count = 0
kakao_count = 0

for item in data:
    orig_src = item.get('original_data', {}).get('original_source', '')
    if orig_src == 'tour_data_12_관광지.json':
        source = item.get('source')
        if source == 'fallback':
            fallback_count += 1
            cat = item.get('category', '')
            tour_cats['FALLBACK: ' + cat] += 1
        else:
            kakao_count += 1
            cat = item.get('category', '')
            tour_cats['KAKAO: ' + cat] += 1
            
        if random.random() < 0.005:
            samples.append(item)

print(f'Total Kakao matched: {kakao_count}')
print(f'Total Fallback (No Match): {fallback_count}')
print('\n--- Top 20 Categories for 관광지 ---')
for k, v in tour_cats.most_common(20):
    print(f'{v}: {k}')

print('\n--- Random Samples ---')
for s in samples[:10]:
    print(f"Title: {s['title']} | Category: {s['category']} | Original: {s['original_data'].get('original_title')}")
