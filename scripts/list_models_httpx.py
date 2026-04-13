import httpx
import os
import json
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY")
url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"

print(f"Fetching models from: {url.replace(api_key, 'REDACTED')}")
try:
    response = httpx.get(url)
    if response.status_code == 200:
        models = response.json().get('models', [])
        print("\nAvailable Models:")
        for m in models:
            if 'embedContent' in m.get('supportedGenerationMethods', []):
                print(f"- {m['name']} ({m['displayName']})")
    else:
        print(f"Error {response.status_code}: {response.text}")
except Exception as e:
    print(f"Connection Error: {e}")
