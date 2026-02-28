"""
HumanlyAI - Standalone Backend Server
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from humanize import router as humanize_router
from config import get_settings

settings = get_settings()

app = FastAPI(
    title="HumanlyAI API",
    description="AI Content Humanization API",
    version="1.0.0",
)

# CORS - Allow all origins for development, restrict in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include the humanize router
app.include_router(humanize_router)


@app.get("/")
async def root():
    return {
        "name": "HumanlyAI API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": [
            "POST /humanizer - Humanize text or file",
            "POST /extract-text - Extract text from file",
            "GET /health - Health check",
        ]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=settings.host, port=settings.port, reload=True)
