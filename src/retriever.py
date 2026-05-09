import json
import os
import chromadb
from chromadb.utils import embedding_functions

CHROMA_PATH = os.path.join(os.path.dirname(__file__), "..", "chroma_db")
DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "shl_product_catalog.json")

def initialize_db():
    print("Initializing Vector Database...")
    chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)
    
    # We use sentence-transformers all-MiniLM-L6-v2 which is fast and lightweight
    sentence_transformer_ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
    
    collection = chroma_client.get_or_create_collection(
        name="shl_assessments",
        embedding_function=sentence_transformer_ef
    )
    
    # Check if we already have data
    if collection.count() > 0:
        print(f"Collection already has {collection.count()} items.")
        return collection

    with open(DATA_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f, strict=False)
    
    documents = []
    metadatas = []
    ids = []
    
    for i, item in enumerate(data):
        name = item.get("name", "")
        desc = item.get("description", "")
        keys = ", ".join(item.get("keys", []))
        job_levels = ", ".join(item.get("job_levels", []))
        
        # Determine a test_type for the recommendation schema based on keys.
        # It seems 'P' = Personality & Behavior, 'K' = Knowledge & Skills, 'S' = Simulations, etc.
        test_type = "U" # Unknown
        if "Personality & Behavior" in keys:
            test_type = "P"
        elif "Knowledge & Skills" in keys:
            test_type = "K"
        elif "Simulations" in keys:
            test_type = "S"
        elif "Ability & Aptitude" in keys:
            test_type = "A"
        elif "Competencies" in keys:
            test_type = "C"
            
        doc_text = f"Assessment Name: {name}\nDescription: {desc}\nCategories: {keys}\nJob Levels: {job_levels}"
        
        documents.append(doc_text)
        metadatas.append({
            "name": name,
            "url": item.get("link", ""),
            "test_type": test_type,
            "keys": keys,
            "job_levels": job_levels,
            "description": desc
        })
        ids.append(str(item.get("entity_id", f"doc_{i}")))
        
    print(f"Adding {len(documents)} documents to ChromaDB...")
    
    # Add in batches to avoid any limits
    batch_size = 100
    for i in range(0, len(documents), batch_size):
        collection.add(
            documents=documents[i:i+batch_size],
            metadatas=metadatas[i:i+batch_size],
            ids=ids[i:i+batch_size]
        )
        print(f"Added batch {i//batch_size + 1}")
        
    print("Database initialization complete.")
    return collection

def get_collection():
    chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)
    sentence_transformer_ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
    return chroma_client.get_collection(name="shl_assessments", embedding_function=sentence_transformer_ef)

if __name__ == "__main__":
    initialize_db()
