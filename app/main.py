from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import json
import datetime

app = FastAPI(title="Research Agent API", version="1.0.0")

@app.get("/")
async def root():
    return {"message": "Research Agent API is running!", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.datetime.now().isoformat()}

@app.post("/research")
async def research(request: Request):
    body = await request.json()
    user = body.get("user", "anonymous")
    query = body.get("query", "")
    
    # Log the request
    print(f"[{datetime.datetime.now().isoformat()}] Research request from {user}: {query}")
    
    # Stub response - in production this would call actual research APIs
    response = {
        "user": user,
        "query": query,
        "status": "completed",
        "results": {
            "sources": [
                {"title": "Wikipedia", "url": "https://wikipedia.org", "snippet": "General knowledge"},
                {"title": "Research Paper", "url": "https://arxiv.org", "snippet": "Academic source"}
            ],
            "summary": f"This is a stub research result for query: {query or 'No query provided'}. In production, this would contain real research data.",
            "processed_at": datetime.datetime.now().isoformat()
        },
        "request_id": f"req_{datetime.datetime.now().strftime('%Y%m%d_%H0m%S"i}"
    }
    
    return JSONResponse(content=response)

# For local development
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
