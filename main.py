from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.responses import PlainTextResponse

# ✅ VERY IMPORTANT: set BEFORE slowapi import
import os
os.environ["STARLETTE_CONFIG"] = ""

from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.middleware import SlowAPIMiddleware

import requests

# ------------------------------
# App Setup
# ------------------------------
app = FastAPI(title="Trade Opportunities API")

# ------------------------------
# Security + Rate Limiting
# ------------------------------
security = HTTPBasic()

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)

def authenticate(credentials: HTTPBasicCredentials = Depends(security)):
    if credentials.username != "user" or credentials.password != "password":
        raise HTTPException(status_code=401, detail="Unauthorized")
    return credentials.username

# ------------------------------
# Market Data
# ------------------------------
def fetch_market_data(sector: str):
    url = f"https://api.duckduckgo.com/?q={sector}+india+market&format=json"
    try:
        res = requests.get(url, timeout=5)
        data = res.json()
        results = [
            topic["Text"]
            for topic in data.get("RelatedTopics", [])
            if "Text" in topic
        ]
        return results[:5] if results else [f"No relevant market data found for {sector}."]
    except Exception as e:
        return [f"Error fetching market data: {e}"]

# ------------------------------
# Gemini AI
# ------------------------------
def analyze_market(sector: str, market_data: list):
    API_KEY = os.getenv("GEMINI_API_KEY")

    if not API_KEY:
        return "Gemini API key not set."

    prompt = f"""
    Analyze the {sector} sector in India based on this data:
    {market_data}

    Provide trade opportunities in bullet points.
    """

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={API_KEY}"

    payload = {
        "contents": [{"parts": [{"text": prompt}]}]
    }

    try:
        res = requests.post(url, json=payload)
        data = res.json()
        return data["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        return f"AI analysis failed: {e}"

# ------------------------------
# Markdown
# ------------------------------
def generate_markdown(sector: str, market_data: list, analysis: str):
    md = f"# Trade Opportunities Report: {sector.title()}\n\n"

    md += "## Market Data\n"
    for item in market_data:
        md += f"- {item}\n"

    md += "\n## AI Analysis\n"
    md += analysis

    return md

# ------------------------------
# Endpoint
# ------------------------------
@app.get("/analyze/{sector}", response_class=PlainTextResponse)
@limiter.limit("3/minute")
async def analyze_sector(
    request: Request,
    sector: str,
    username: str = Depends(authenticate)
):
    if not sector.isalpha():
        raise HTTPException(status_code=400, detail="Invalid sector name")

    market_data = fetch_market_data(sector)
    analysis = analyze_market(sector, market_data)
    return generate_markdown(sector, market_data, analysis)

# ------------------------------
# Root
# ------------------------------
@app.get("/")
def root():
    return {"message": "API running"}