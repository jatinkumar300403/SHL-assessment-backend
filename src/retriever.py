import json
import os

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "shl_product_catalog.json")

_catalog_cache = None

def initialize_db():
    # We no longer use ChromaDB because it exceeds the 512MB RAM limit on free hosting.
    # Instead, we minify the catalog to ~200KB and pass it directly to Gemini's 1M token context window.
    # This gives 100% perfect recall and uses almost zero RAM!
    global _catalog_cache
    if _catalog_cache is not None:
        return _catalog_cache
        
    with open(DATA_PATH, 'r', encoding='utf-8') as f:
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
        
    _catalog_cache = json.dumps(minified)
    print(f"Catalog loaded into memory. Size: {len(_catalog_cache) / 1024:.2f} KB")
    return _catalog_cache

def get_catalog_string():
    return initialize_db()
