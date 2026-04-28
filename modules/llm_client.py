import os
import json
from dotenv import load_dotenv
from groq import Groq
from modules.prompts import build_prompt

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY is missing from .env file.")

# Initialize the Groq client
client = Groq(
    api_key=GROQ_API_KEY,
)

def generate_ddr_content(parsed_data, **kwargs):
    # Construct the prompt and call Groq to generate the report JSON
    print("Building prompt from parsed text data...")
    prompt = build_prompt(parsed_data)
    
    print("Sending request to Groq API (this is usually very fast)...")
    max_retries = 3
    retry_delay = 5
    
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": "You are an expert Building Diagnostics Engineer. Output strictly valid JSON without any markdown formatting."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
            )
            
            raw_response = response.choices[0].message.content
            
            try:
                report_data = json.loads(raw_response)
                return report_data
            except json.JSONDecodeError as e:
                print(f"Failed to parse JSON from LLM. Raw response:\n{raw_response}")
                raise e
                
        except Exception as e:
            error_str = str(e).lower()
            if "429" in error_str or "rate limit" in error_str:
                if attempt < max_retries - 1:
                    print(f"Rate limit hit. Waiting {retry_delay}s before retry {attempt + 1}/{max_retries}...")
                    import time
                    time.sleep(retry_delay)
                    continue
            print(f"API call failed on attempt {attempt + 1}: {e}")
            raise e
