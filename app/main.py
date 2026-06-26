from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse, HTMLResponse
import uvicorn
import httpx
from bs4 import BeautifulSoup

app = FastAPI(
    title="Scraper API",
    description="Kleinanzeigen & General Web Scraper",
    version="1.0.0"
)

# ====================== DASHBOARD ======================
@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    html = """
    <html>
    <head>
        <title>Scraper API Dashboard</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; background: #f0f2f5; }
            h1 { color: #1a73e8; }
            .card { background: white; padding: 25px; margin: 20px 0; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); }
            input { width: 100%; padding: 12px; font-size: 16px; border: 1px solid #ddd; border-radius: 8px; }
            button { padding: 14
