import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    print("GOOGLE_API_KEY not found in .env")
else:
    genai.configure(api_key=api_key)
    try:
        print(f"Listing models for key: {api_key[:5]}...")
        for m in genai.list_models():
            if 'embedContent' in m.supported_generation_methods:
                print(f"Model: {m.name} - {m.display_name}")
    except Exception as e:
        print(f"Error: {e}")
