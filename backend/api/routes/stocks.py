from fastapi import APIRouter, HTTPException
from typing import Dict
from services.database import db_service

router = APIRouter()

@router.get("/{symbol}", response_model=Dict)
async def get_stock_info(symbol: str):
    """Get information about a specific stock"""
    try:
        stock_info = await db_service.get_stock_info(symbol)
        if not stock_info:
            raise HTTPException(status_code=404, detail=f"Stock {symbol} not found")
        return stock_info
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 