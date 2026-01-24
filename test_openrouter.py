#!/usr/bin/env python3
"""
Quick test script for OpenRouter connection
"""

import os
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
if not OPENROUTER_API_KEY:
    print("❌ Error: OPENROUTER_API_KEY not found in .env file")
    exit(1)

client = OpenAI(
    api_key=OPENROUTER_API_KEY,
    base_url="https://openrouter.ai/api/v1",
)

system_prompt = "You are a helpful assistant that answers in 2 concise bullet points."
user_message = "Give me 2 ideas for a cozy rainy-day activity at home."

print("Testing OpenRouter connection...")
print(f"Model: nvidia/nemotron-3-nano-30b-a3b:free")
print(f"System: {system_prompt}")
print(f"User: {user_message}\n")

try:
    response = client.chat.completions.create(
        model="nvidia/nemotron-3-nano-30b-a3b:free",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
    )
    
    print("✅ Connection successful!")
    print(f"Response: {response.choices[0].message.content}")
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
