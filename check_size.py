import json

with open('data/shl_product_catalog.json', 'r', encoding='utf-8') as f:
    data = json.load(f, strict=False)

minified = []
for item in data:
    keys = ", ".join(item.get("keys", []))
    test_type = "U"
    if "Personality & Behavior" in keys: test_type = "P"
    elif "Knowledge & Skills" in keys: test_type = "K"
    elif "Simulations" in keys: test_type = "S"
    elif "Ability & Aptitude" in keys: test_type = "A"
    elif "Competencies" in keys: test_type = "C"
        
    minified.append({
        "name": item.get("name"),
        "url": item.get("link"),
        "test_type": test_type,
        "desc": item.get("description"),
        "levels": item.get("job_levels_raw")
    })

min_json = json.dumps(minified)
print(f"Minified size: {len(min_json) / 1024:.2f} KB")
