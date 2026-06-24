import json
import sys

input_file = 'data/unified_dataset.json'
output_file = 'data/unified_dataset.json'

with open(input_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

original_count = len(data)
filtered_data = []
agency_count = 0
festival_count = 0

for item in data:
    cat = item.get('category', '')
    
    # Filter out travel agencies
    if cat and '여행사' in cat:
        agency_count += 1
        continue
        
    # Update festival categories
    if item.get('source') == 'tour_api_festival':
        item['category'] = '문화, 예술 > 축제/공연/행사'
        festival_count += 1
        
    filtered_data.append(item)

with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(filtered_data, f, ensure_ascii=False, indent=2)

print(f"Original count: {original_count}")
print(f"Removed {agency_count} travel agencies.")
print(f"Updated category for {festival_count} festival items.")
print(f"Final count: {len(filtered_data)}")
