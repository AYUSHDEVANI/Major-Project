import google.generativeai as genai
import os

# Manual .env parsing availability
def get_key():
    try:
        with open(".env", "r") as f:
            for line in f:
                if line.startswith("GOOGLE_API_KEY="):
                    return line.split("=", 1)[1].strip()
    except:
        return None

key = get_key()
if not key:
    key = os.getenv("GOOGLE_API_KEY")

if not key:
    with open("models.txt", "w") as f:
        f.write("ERROR: NO API KEY FOUND")
    exit(1)

genai.configure(api_key=key)

try:
    with open("models.txt", "w") as f:
        f.write("Available Models:\n")
        for m in genai.list_models():
            f.write(f"{m.name}\n")
            f.write(f"  Methods: {m.supported_generation_methods}\n")
except Exception as e:
    with open("models.txt", "w") as f:
        f.write(f"ERROR LISTING MODELS: {e}")
