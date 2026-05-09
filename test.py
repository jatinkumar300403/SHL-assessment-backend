import requests

url = "http://localhost:8000/chat"
payload = {
    "messages": [
        {
            "role": "user",
            "content": "Looking for a frontend engineer skilled in React",
        },
        {
            "role": "assistant",
            "content": "Got it. What level of experience are you targeting?",
        },
        {"role": "user", "content": "Someone with 2-3 years experience"},
    ]
}

response = requests.post(url, json=payload)
print(response.json())
