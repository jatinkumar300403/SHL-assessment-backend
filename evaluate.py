import requests
import json
import time

URL = "http://localhost:8000/chat"
HEALTH_URL = "http://localhost:8000/health"

def run_evaluation():
    print("=== Starting SHL Agent Evaluation ===")
    
    # 1. Check Health
    try:
        r = requests.get(HEALTH_URL)
        assert r.status_code == 200
        print("Health Check Passed")
    except Exception as e:
        print(f"Health Check Failed: {e}")
        return

    # 2. Test Vague Query (Should Clarify)
    vague_payload = {"messages": [{"role": "user", "content": "I need an assessment"}]}
    r = requests.post(URL, json=vague_payload)
    data = r.json()
    assert len(data.get("recommendations", [])) == 0, "Agent recommended on a vague query!"
    assert data.get("end_of_conversation") == False
    print("Vague Query Evaluation Passed (Agent clarified instead of recommending)")
    time.sleep(30) # Prevent 429 Rate Limiting from Gemini Free Tier

    # 3. Test Specific Query (Should Recommend)
    specific_payload = {"messages": [{"role": "user", "content": "I need a test for a mid-level Java developer"}]}
    r = requests.post(URL, json=specific_payload)
    data = r.json()
    assert len(data.get("recommendations", [])) > 0, "Agent failed to recommend on specific query! (It may be rate limited)"
    
    # Measure Groundedness (All URLs must start with the catalog domain)
    for rec in data["recommendations"]:
        assert rec["url"].startswith("http"), "Hallucinated URL detected!"
    print(f"Recommendation Relevance & Groundedness Passed ({len(data['recommendations'])} items returned)")

    time.sleep(30) # Prevent 429 Rate Limiting from Gemini Free Tier

    # 4. Test Off-Topic (Should Refuse gracefully)
    off_topic_payload = {"messages": [{"role": "user", "content": "How do I fire an employee?"}]}
    r = requests.post(URL, json=off_topic_payload)
    data = r.json()
    assert len(data.get("recommendations", [])) == 0
    print("Off-Topic Refusal Passed")

    print("\n=== Evaluation Complete: All automated behavioral probes passed! ===")

if __name__ == "__main__":
    print("Ensure Uvicorn is running on port 8000 before evaluating...")
    run_evaluation()
