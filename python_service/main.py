import os
import re
import hashlib
from datetime import datetime
from typing import List, Optional
import requests
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(
    title="Lead Discovery & Text Processing Microservice",
    description="Python microservice supporting n8n workflow for text normalization, search execution, and deduplication hashing.",
    version="1.0.0"
)

# ------------------------------------------------------------------------------
# Request & Response Models
# ------------------------------------------------------------------------------

class CollectRequest(BaseModel):
    platform: str = Field(default="linkedin", description="Target platform (linkedin, threads, facebook, web)")
    keywords: List[str] = Field(default_factory=list, description="Matched keywords dictionary")
    queries: List[str] = Field(default_factory=list, description="Target search query strings")
    max_results: int = Field(default=10, description="Max results per query")

class CandidateLead(BaseModel):
    platform: str
    post_url: str
    author_name: Optional[str] = None
    author_url: Optional[str] = None
    post_text: str
    posted_at: str
    matched_keywords: List[str]
    source_query: str
    post_text_hash: str

class CollectResponse(BaseModel):
    status: str
    total_collected: int
    candidates: List[CandidateLead]

class NormalizeRequest(BaseModel):
    text: str
    url: Optional[str] = None

class NormalizeResponse(BaseModel):
    cleaned_text: str
    text_hash: str
    url: Optional[str]

# ------------------------------------------------------------------------------
# Utility Helpers
# ------------------------------------------------------------------------------

def clean_text(raw_text: str) -> str:
    """Normalize whitespace, remove control characters, and clean messy formatting."""
    if not raw_text:
        return ""
    # Remove HTML tags if present
    text = re.sub(r'<[^>]+>', ' ', raw_text)
    # Replace multiple spaces/newlines with a single space
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def compute_hash(text: str) -> str:
    """Compute SHA-256 hash of lowercase cleaned text for content deduplication."""
    cleaned = clean_text(text).lower()
    return hashlib.sha256(cleaned.encode('utf-8')).hexdigest()

def detect_platform(url: str) -> str:
    url_lower = url.lower()
    if 'linkedin.com' in url_lower:
        return 'linkedin'
    elif 'threads.net' in url_lower:
        return 'threads'
    elif 'facebook.com' in url_lower:
        return 'facebook'
    return 'web'

# ------------------------------------------------------------------------------
# API Endpoints
# ------------------------------------------------------------------------------

@app.get("/health")
def health_check():
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}

@app.post("/api/v1/normalize", response_model=NormalizeResponse)
def normalize_text_endpoint(req: NormalizeRequest):
    cleaned = clean_text(req.text)
    text_hash = compute_hash(cleaned)
    return NormalizeResponse(
        cleaned_text=cleaned,
        text_hash=text_hash,
        url=req.url
    )

@app.post("/api/v1/collect", response_model=CollectResponse)
def collect_leads_endpoint(req: CollectRequest):
    serper_api_key = os.getenv("SEARCH_API_KEY", "")
    candidates = []
    seen_urls = set()

    for query_str in req.queries:
        if not serper_api_key:
            # If no API key configured, return mock structure for workflow safety
            continue

        try:
            resp = requests.post(
                "https://google.serper.dev/search",
                headers={
                    "X-API-KEY": serper_api_key,
                    "Content-Type": "application/json"
                },
                json={
                    "q": query_str,
                    "num": min(req.max_results, 10),
                    "tbs": "qdr:w"
                },
                timeout=10
            )
            if resp.status_code != 200:
                continue

            data = resp.json()
            organic_results = data.get("organic", [])

            for item in organic_results:
                link = item.get("link", "")
                if not link or link in seen_urls:
                    continue

                seen_urls.add(link)
                title = item.get("title", "")
                snippet = item.get("snippet", "")
                combined_text = clean_text(f"{title} {snippet}")
                
                if not combined_text:
                    continue

                # Match keywords found in text
                found_kws = [kw for kw in req.keywords if kw.lower() in combined_text.lower()]
                
                # Author extraction heuristic from title/url
                author_name = None
                if "linkedin.com/posts/" in link:
                    parts = link.split("/posts/")
                    if len(parts) > 1:
                        author_name = parts[1].split("-")[0].capitalize()

                candidates.append(CandidateLead(
                    platform=detect_platform(link),
                    post_url=link,
                    author_name=author_name or "Public Poster",
                    author_url=link if "profile" in link or "in/" in link else None,
                    post_text=combined_text,
                    posted_at=item.get("date") or datetime.utcnow().isoformat(),
                    matched_keywords=found_kws if found_kws else req.keywords[:2],
                    source_query=query_str,
                    post_text_hash=compute_hash(combined_text)
                ))

        except Exception as err:
            # Log & isolate failure per query
            print(f"Error querying '{query_str}': {err}")

    return CollectResponse(
        status="success",
        total_collected=len(candidates),
        candidates=candidates
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
