import os
import json
from collections import defaultdict, Counter

dataset_dir = 'dataset'
unified_file = 'data/unified_dataset.json'

# 1. Build original title to cat3 mapping
# Since title might not be perfectly unique, we map (original_source, title) -> cat3
orig_to_cat3 = {}

for f_name in os.listdir(dataset_dir):
    if not f_name.endswith('.json') or 'tour_data' not in f_name:
        continue
    path = os.path.join(dataset_dir, f_name)
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        for item in data:
            title = item.get('title')
            cat3 = item.get('cat3') or item.get('cat2') or item.get('cat1') or ''
            if title and cat3:
                orig_to_cat3[(f_name, title)] = cat3

print(f"Loaded {len(orig_to_cat3)} original items with category codes.")

with open(unified_file, 'r', encoding='utf-8') as f:
    unified_data = json.load(f)

# 2. Build cat3 to Kakao category frequency mapping
cat3_to_kakao = defaultdict(Counter)

for item in unified_data:
    if item.get('source') == 'kakao':
        orig_source = item.get('original_data', {}).get('original_source')
        orig_title = item.get('original_data', {}).get('original_title')
        kakao_cat = item.get('category')
        if orig_source and orig_title and kakao_cat:
            cat3 = orig_to_cat3.get((orig_source, orig_title))
            if cat3:
                cat3_to_kakao[cat3][kakao_cat] += 1

# 3. Create the best Kakao category mapping for each cat3
cat3_mapping = {}
for cat3, counts in cat3_to_kakao.items():
    best_cat = counts.most_common(1)[0][0]
    cat3_mapping[cat3] = best_cat

print(f"Built mapping for {len(cat3_mapping)} category codes.")
for k, v in list(cat3_mapping.items())[:10]:
    print(f"  {k} -> {v}")

# Default fallbacks
default_fallbacks = {
    'tour_data_12_관광지.json': '여행 > 관광,명소',
    'tour_data_14_문화시설.json': '문화,예술 > 문화시설',
    'tour_data_28_레포츠.json': '스포츠,레저 > 레포츠',
    'tour_data_32_숙박.json': '여행 > 숙박',
    'tour_data_38_쇼핑.json': '가정,생활 > 쇼핑',
    'tour_data_39_음식점.json': '음식점'
}

# 4. Patch the fallback data
fallback_updated = 0
for item in unified_data:
    if item.get('source') == 'fallback':
        orig_source = item.get('original_data', {}).get('original_source')
        orig_title = item.get('original_data', {}).get('original_title')
        
        # Try to find its cat3
        cat3 = orig_to_cat3.get((orig_source, orig_title))
        
        # Determine the detailed category
        detailed_cat = ''
        if cat3 and cat3 in cat3_mapping:
            detailed_cat = cat3_mapping[cat3]
        else:
            detailed_cat = default_fallbacks.get(orig_source, '기타')
            
        item['category'] = detailed_cat
        fallback_updated += 1

with open(unified_file, 'w', encoding='utf-8') as f:
    json.dump(unified_data, f, ensure_ascii=False, indent=2)

print(f"Updated detailed categories for {fallback_updated} fallback items.")
