from fastapi import APIRouter, HTTPException
from typing import Dict, List
from services.database import db_service

router = APIRouter()

@router.get("/{scheme_name}", response_model=Dict)
async def get_fund_info(scheme_name: str):
    """Get information about a specific mutual fund"""
    try:
        fund_info = await db_service.get_fund_info(scheme_name)
        if not fund_info:
            raise HTTPException(status_code=404, detail=f"Fund {scheme_name} not found")
        return fund_info
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{scheme_name}/holdings", response_model=List[Dict])
async def get_fund_holdings(scheme_name: str):
    """Get holdings information for a specific mutual fund"""
    try:
        holdings = await db_service.get_holdings_data(scheme_name)
        if not holdings:
            raise HTTPException(status_code=404, detail=f"Holdings for fund {scheme_name} not found")
        return holdings
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 