import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=api_key)

try:
    with open("available_models.txt", "w") as f:
        f.write(f"Library Version: {genai.__version__}\n")
        f.write("MODELS:\n")
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                f.write(f"{m.name}\n")
except Exception as e:
    with open("available_models.txt", "w") as f:
        f.write(f"ERROR: {e}")
