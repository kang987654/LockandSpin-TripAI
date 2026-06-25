import os
import json

dataset_dir = 'dataset'
unified_file = 'data/unified_dataset.json'

# 1. Build original title to firstimage mapping
orig_to_image = {}

for f_name in os.listdir(dataset_dir):
    if not f_name.endswith('.json') or 'tour_data' not in f_name:
        continue
    path = os.path.join(dataset_dir, f_name)
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        for item in data:
            title = item.get('title')
            # firstimage might be empty string
            img = item.get('firstimage') or item.get('firstimage2')
            if title and img:
                orig_to_image[(f_name, title)] = img

print(f"Loaded {len(orig_to_image)} original items with images.")

with open(unified_file, 'r', encoding='utf-8') as f:
    unified_data = json.load(f)

# 2. Patch images and count
has_image = 0
no_image = 0
naver_no_image = 0
tour_no_image = 0

for item in unified_data:
    orig_source = item.get('original_data', {}).get('original_source')
    orig_title = item.get('original_data', {}).get('original_title')
    
    # Check if we already put image in URL for festivals
    if item.get('source') == 'tour_api_festival':
        img = item.get('url')
        if img and img.startswith('http'):
            item['image_url'] = img
    
    if 'image_url' not in item:
        # Try to find its original image
        img = orig_to_image.get((orig_source, orig_title))
        if img:
            item['image_url'] = img

    # Count statistics
    if item.get('image_url'):
        has_image += 1
    else:
        no_image += 1
        if orig_source and 'naver_data' in orig_source:
            naver_no_image += 1
        else:
            tour_no_image += 1

with open(unified_file, 'w', encoding='utf-8') as f:
    json.dump(unified_data, f, ensure_ascii=False, indent=2)

print(f"Successfully patched unified dataset.")
print(f"Total items with images: {has_image}")
print(f"Total items without images: {no_image}")
print(f"  - Missing from Naver data: {naver_no_image}")
print(f"  - Missing from Tour API data: {tour_no_image}")
