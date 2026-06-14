from fastapi import FastAPI, Request, HTTPException

from fastapi.responses import JSONResponse

import httpx

import json

import datetime

import os

import uuid



app = FastAPI(title="Research Agent API", version="1.2.0")



NOTION_TOKEN = os.getenv("NOTION_TOKEN", "")

NOTION_DB_ID = os.getenv("NOTION_DB_ID", "37f436e7-6f7e-8147-95df-c77c840944a3")



async def search_wikipedia(query: str, limit: int = 3):
    
    async with httpx.AsyncClient() as client:
        
        resp = await client.get(
            
            "https://en.wikipedia.org/w/api.php",
            
            params={
                
                "action": "query",
                
                "list": "search",
                
                "srsearch": query,
                
                "format": "json",
                
                "srlimit": limit,
                
                "prop": "extracts",
                
                "exintro": True,
                
                "explaintext": True
                
            },
            
            timeout=10
            
        )
        
        data = resp.json()
        
        results = []
        
        for r in data.get("query", {}).get("search", []):
            
            results.append({
                
                "title": r["title"],
                
                "snippet": r.get("snippet", "").replace("<span class=\"searchmatch\">", "").replace("</span>", ""),
                
                "url": f"https://en.wikipedia.org/wiki/{r['title'].replace(' ', '_')}"
                
            })
            
        return results
        


async def search_duckduckgo(query: str):
    
    async with httpx.AsyncClient() as client:
        
        resp = await client.get(
            
            "https://api.duckduckgo.com/",
            
            params={"q": query, "format": "json", "no_html": 1, "skip_disambig": 1},
            
            timeout=10
            
        )
        
        data = resp.json()
        
        results = []
        
        abstract = data.get("AbstractText", "")
        
        if abstract:
            
            results.append({
                
                "title": data.get("Heading", query),
                
                "snippet": abstract[:500],
                
                "url": data.get("AbstractURL", "")
                
            })
            
        for topic in data.get("RelatedTopics", []):
            
            if "Text" in topic:
                
                results.append({
                    
                    "title": topic.get("Text", "").split(" - ")[0][:100],
                    
                    "snippet": topic.get("Text", "")[:500],
                    
                    "url": topic.get("FirstURL", "")
                    
                })
                
            if len(results) >= 5:
                
                break
                
        return results
        


async def save_to_notion(query: str, summary: str, sources: list, status: str = "Complete"):
    
    if not NOTION_TOKEN:
        
        return {"error": "No Notion token configured"}
        


    sources_text = "\n".join([f"{s['title']}: {s['url']}" for s in sources[:10]])
    


    async with httpx.AsyncClient() as client:
        
        resp = await client.post(
            
            "https://api.notion.com/v1/pages",
            
            headers={
                
                "Authorization": f"Bearer {NOTION_TOKEN}",
                
                "Content-Type": "application/json",
                
                "Notion-Version": "2022-06-28"
                
            },
            
            json={
                
                "parent": {"type": "database_id", "database_id": NOTION_DB_ID},
                
                "properties": {
                    
                    "Query": {
                        
                        "title": [{"type": "text", "text": {"content": query[:100]}}]
                        
                    },
                    
                    "Summary": {
                        
                        "rich_text": [{"type": "text", "text": {"content": summary[:1900]}}]
                        
                    },
                    
                    "Sources": {
                        
                        "rich_text": [{"type": "text", "text": {"content": sources_text[:1900]}}]
                        
                    },
                    
                    "Status": {
                        
                        "select": {"name": status}
                        
                    },
                    
                    "Timestamp": {
                        
                        "date": {"start": datetime.datetime.now().isoformat()}
                        
                    }
                    
                }
                
            },
            
            timeout=10
            
        )
        
        return resp.json()
        


@app.get("/")

async def root():
    
    notion_status = "connected" if NOTION_TOKEN else "not configured"
    
    return {
        
        "message": "Research Agent API is running!",
        
        "version": "1.2.0",
        
        "notion": notion_status,
        
        "endpoints": {
            
            "/health": "Health check",
            
            "/research": "POST - Run a research query",
            
            "/test": "GET - Test Notion integration"
            
        }
        
    }
    


@app.get("/health")

async def health_check():
    
    return {"status": "healthy", "timestamp": datetime.datetime.now().isoformat()}
    


@app.get("/test")

async def test_notion():
    
    result = await save_to_notion(
        
        query="Test entry from Research Agent API",
        
        summary="This is an automated test to verify Notion database integration.",
        
        sources=[{"title": "API Test", "url": "https://github.com/Nitesh1221/agent-research"}]
        
    )
    
    if "error" in result:
        
        return {"status": "error", "detail": result["error"]}
        
    return {"status": "ok", "page_id": result.get("id", "")}
    


@app.post("/research")

async def research(request: Request):
    
    try:
        
        body = await request.json()
        
    except Exception:
        
        body = {}
        


    user = body.get("user", "anonymous")
    
    query = body.get("query", "").strip()
    


    if not query:
        
        return JSONResponse(
            
            content={"error": "query is required", "user": user, "status": "failed"},
            
            status_code=400
            
        )
        


    req_id = f"req_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"
    
    print(f"[{datetime.datetime.now().isoformat()}] [{req_id}] Research: {user} -> {query}")
    


    try:
        
        wiki_results = await search_wikipedia(query)
        
        ddg_results = await search_duckduckgo(query)
        
    except Exception as e:
        
        print(f"[{req_id}] Search error: {e}")
        
        wiki_results = []
        
        ddg_results = []
        


    all_sources = wiki_results + ddg_results
    
    seen_titles = set()
    
    unique_sources = []
    
    for s in all_sources:
        
        if s["title"] not in seen_titles:
            
            seen_titles.add(s["title"])
            
            unique_sources.append(s)
            


    summary_parts = []
    
    for s in unique_sources[:3]:
        
        if s.get("snippet"):
            
            summary_parts.append(f"**{s['title']}**: {s['snippet'][:200]}")
            


    summary = " | ".join(summary_parts) if summary_parts else f"No results found for: {query}"
    


    response = {
        
        "user": user,
        
        "query": query,
        
        "status": "completed",
        
        "request_id": req_id,
        
        "results": {
            
            "sources": unique_sources[:10],
            
            "summary": summary,
            
            "source_count": len(unique_sources),
            
            "processed_at": datetime.datetime.now().isoformat()
            
        }
        
    }
    


    try:
        
        notion_result = await save_to_notion(query, summary, unique_sources[:10])
        
        response["notion_page"] = notion_result.get("id", "") if "id" in notion_result else "failed"
        
    except Exception as e:
        
        print(f"[{req_id}] Notion save error: {e}")
        
        response["notion_page"] = "failed"
        


    return JSONResponse(content=response)
    


@app.post("/research/batch")

async def research_batch(request: Request):
    
    body = await request.json()
    
    queries = body.get("queries", [])
    
    user = body.get("user", "anonymous")
    


    if not queries:
        
        return JSONResponse(content={"error": "queries list is required", "status": "failed"}, status_code=400)
        


    results = []
    
    for q in queries:
        
        mock_req = Request(scope={"type": "http", "method": "POST"})
        
        mock_req._body = json.dumps({"user": user, "query": q}).encode()
        
        res = await research(mock_req)
        
        results.append(res.body_dict if hasattr(res, "body_dict") else json.loads(res.body))
        


    return JSONResponse(content={"user": user, "status": "completed", "results": results, "count": len(results)})
    


if __name__ == "__main__":
    
    import uvicorn
    
    uvicorn.run(app, host="0.0.0.0", port=8000)















































































































































































