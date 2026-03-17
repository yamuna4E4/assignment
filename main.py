# main.py
from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.responses import PlainTextResponse
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.middleware import SlowAPIMiddleware

app = FastAPI(title="Trade Opportunities API")

# ------------------------------
# Security & Rate Limiting
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
# Data Collection (Dummy)
# ------------------------------
def fetch_market_data(sector: str):
    """Return mock market data for demo purposes."""
    return [
        f"No relevant market data found for {sector}."
    ]

# ------------------------------
# AI Analysis (Mocked)
# ------------------------------
def analyze_market(sector: str, market_data: list):
    """Mock AI analysis to prevent server crash."""
    return (
        f"AI analysis for {sector.title()} sector:\n"
        f"- Trade opportunity 1\n"
        f"- Trade opportunity 2\n"
        f"- Trade opportunity 3"
    )

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
@limiter.limit("3/minute")
async def analyze_sector(
    request: Request,            # <-- Add this
    sector: str,
    username: str = Depends(authenticate)
):
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

from starlette.config import Config
from slowapi import Limiter
from slowapi.util import get_remote_address

# Disable automatic .env loading
config = Config(environ={})  # Pass empty environment to avoid .env
limiter = Limiter(key_func=get_remote_address, app_config=config)