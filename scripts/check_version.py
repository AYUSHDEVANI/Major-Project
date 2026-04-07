import google.generativeai as genai
import langchain_google_genai

print(f"google-generativeai version: {genai.__version__}")
try:
    print(f"langchain-google-genai version: {langchain_google_genai.__version__}")
except:
    print("langchain-google-genai version: unknown")
