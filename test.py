# test_gemini_key.py
import os
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables from .env
load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("❌ GEMINI_API_KEY not found in .env file")

# Configure the Gemini API
genai.configure(api_key=api_key)

# Create a model instance
model = genai.GenerativeModel("models/gemini-2.5-flash")

# Try a simple prompt
try:
    response = model.generate_content("Say hello from Gemini!")
    print("✅ API Key works! Response from Gemini:")
    print(response.text)
except Exception as e:
    print("❌ API key test failed.")
    print(e)
