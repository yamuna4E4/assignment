# main.py

from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.responses import PlainTextResponse
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.middleware import SlowAPIMiddleware
import requests
import openai
import os

# ------------------------------
# Configuration
# ------------------------------

openai.api_key = os.getenv("OPENAI_API_KEY")  

app = FastAPI(title="Trade Opportunities API")
security = HTTPBasic()
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)

# ------------------------------
# Authentication
# ------------------------------

def authenticate(credentials: HTTPBasicCredentials = Depends(security)):
    if credentials.username != "user" or credentials.password != "password":
        raise HTTPException(status_code=401, detail="Unauthorized")
    return credentials.username

# ------------------------------
# Data Collection
# ------------------------------

def fetch_market_data(sector: str):
    """
    Fetch top 5 news/market data items for the given sector from DuckDuckGo API.
    """
    url = f"https://api.duckduckgo.com/?q={sector}+india+market&format=json"
    try:
        resp = requests.get(url, timeout=5)
        resp.raise_for_status()
        data = resp.json()
        results = [r["Text"] for r in data.get("RelatedTopics", []) if "Text" in r]
        return results[:5] if results else [f"No relevant market data found for {sector}."]
    except Exception as e:
        return [f"Error fetching market data: {e}"]

# ------------------------------
# AI Analysis
# ------------------------------

def analyze_market(sector: str, market_data: list):
    """
    Use OpenAI GPT-4 to analyze market data for the sector
    """
    prompt = f"Analyze the following market data for the {sector} sector in India and provide trade opportunities:\n\n"
    prompt += "\n".join(market_data)
    
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500
        )
        analysis = response.choices[0].message.content
        return analysis
    except Exception as e:
        return f"Error during AI analysis: {e}"

# ------------------------------
# Markdown Report Generation
# ------------------------------

def generate_markdown(sector: str, market_data: list, analysis: str):
    md = f"# Trade Opportunities Report: {sector.title()}\n\n"
    md += "## Market Data\n"
    for item in market_data:
        md += f"- {item}\n"
    md += "\n## AI Analysis\n"
    md += f"{analysis}\n"
    return md

# ------------------------------
# API Endpoint
# ------------------------------
from fastapi import Request

@app.get("/analyze/{sector}", response_class=PlainTextResponse)
@limiter.limit("3/minute")  # Rate limit: 3 requests per minute per IP
async def analyze_sector(sector: str, request: Request, username: str = Depends(authenticate)):
    # Input validation
    if not sector.isalpha():
        raise HTTPException(status_code=400, detail="Sector name must be alphabetic")
    
    # Fetch market data
    market_data = fetch_market_data(sector)
    
    # AI analysis
    analysis = analyze_market(sector, market_data)
    
    # Generate Markdown
    markdown_report = generate_markdown(sector, market_data, analysis)
    
    return markdown_report

# ------------------------------
# Root Endpoint
# ------------------------------

@app.get("/")
def read_root():
    return {"message": "Welcome to Trade Opportunities API. Use /analyze/{sector} endpoint."}