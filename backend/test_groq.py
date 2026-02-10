import httpx
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("LLM_API_KEY")
api_url = os.getenv("LLM_API_URL", "https://api.groq.com/openai/v1")
model = os.getenv("LLM_MODEL", "llama-3.3-70b-versatile")

output = []
output.append(f"Testing Groq with URL: {api_url}")
output.append(f"Model: {model}")
output.append(f"Key Prefix: {api_key[:10]}..." if api_key else "NO KEY")

url = f"{api_url.rstrip('/')}/chat/completions"
headers = {"Authorization": f"Bearer {api_key}"}
payload = {
    "model": model,
    "messages": [{"role": "user", "content": "Hello, respond with 'OK'"}],
    "max_tokens": 10
}

try:
    with httpx.Client(timeout=10.0) as client:
        response = client.post(url, headers=headers, json=payload)
        output.append(f"Status Code: {response.status_code}")
        if response.status_code != 200:
            output.append(f"Error Response Body: {response.text}")
        else:
            output.append(f"Success! Response: {response.json()['choices'][0]['message']['content']}")
except Exception as e:
    output.append(f"Exception: {e}")

with open("test_api_manual_output.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(output))
