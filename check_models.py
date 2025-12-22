from google import genai
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    print("Error: GOOGLE_API_KEY not found in .env")
    exit(1)

client = genai.Client(api_key=api_key)

print("Listing available models...")
try:
    for model in client.models.list():
        if "imagen" in model.name or "generate" in model.name:
            print(f"- {model.name} : {model.display_name}")
except Exception as e:
    print(f"Error listing models: {e}")
