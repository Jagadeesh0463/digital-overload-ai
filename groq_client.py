import os
import json
import time
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

def get_api_key():
    try:
        import streamlit as st
        return st.secrets["GROQ_API_KEY"]
    except:
        return os.environ.get("GROQ_API_KEY", "")

client = Groq(api_key=get_api_key())

PROMPT = """You are a student workload analyzer. Read the student's description and extract data.

Return ONLY a valid JSON object with exactly these fields:
{{
  "task_count": <int: total distinct tasks>,
  "urgency_signals": <int: count of urgent keywords like 'due today','urgent','deadline','tonight','ASAP'>,
  "unique_domains": <int: count of distinct domains - max 4: Academic/Social/Personal/Admin>,
  "context_switches": <int: estimated domain-shift transitions today - max 6>,
  "pending_messages": <int: unread or unreplied messages>,
  "energy_level": <str: exactly "High", "Medium", or "Low">,
  "free_hours": <float: free hours today>,
  "estimated_hours": <float: TOTAL hours needed across ALL tasks combined>,
  "start_time": <str: when student starts work e.g. "9 PM", "8 AM", "Now">,
  "tasks": [
    {{"name": <str>, "domain": <str: Academic/Social/Personal/Admin>, "hours": <float>}}
  ]
}}

Rules:
- unique_domains max = 4
- context_switches max = 6
- pending_messages max = 50
- energy_level must be exactly "High", "Medium", or "Low"
- estimated_hours = SUM of all task hours
- Return ONLY the JSON — no explanation, no markdown, no backticks

Student description:
{text}"""


def extract_features(text: str, retries: int = 3) -> dict:
    for attempt in range(retries):
        try:
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "user", "content": PROMPT.format(text=text)}
                ],
                temperature=0.1,
            )
            raw = response.choices[0].message.content.strip()

            # Remove markdown fences if model adds them
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]

            return json.loads(raw.strip())

        except Exception as e:
            if attempt < retries - 1:
                time.sleep(1)
            else:
                raise ValueError(f"Groq failed after {retries} attempts: {e}")
