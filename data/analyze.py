import json
import collections

with open('data/shl_product_catalog.json', 'r', encoding='utf-8') as f:
    data = json.load(f, strict=False)

print(f"Total assessments: {len(data)}")
keys_counter = collections.Counter()
for item in data:
    for k in item.get('keys', []):
        keys_counter[k] += 1

print("Keys distribution:", keys_counter)
