from fastapi import APIRouter, HTTPException
from typing import List, Dict
from services.news_scraper import NewsScraperService
from services.database import db_service

router = APIRouter()
news_scraper = NewsScraperService()

@router.get("/recent", response_model=List[Dict])
async def get_recent_news():
    """Get recent news articles"""
    try:
        return await db_service.get_recent_news()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/entity/{entity_name}", response_model=List[Dict])
async def get_news_by_entity(entity_name: str):
    """Get news articles related to a specific entity"""
    try:
        return await db_service.get_news_by_entity(entity_name)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/refresh")
async def refresh_news():
    """Fetch fresh news from all sources"""
    try:
        news_items = await news_scraper.get_all_news()
        await db_service.store_news(news_items)
        return {"message": f"Successfully fetched {len(news_items)} news articles"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 