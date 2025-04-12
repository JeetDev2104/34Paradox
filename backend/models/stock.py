from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from .base import PyObjectId

class StockBase(BaseModel):
    finCode: str
    bseScripCode: Optional[str] = None
    bseScripName: Optional[str] = None
    name: str
    ticker: str
    sector: Optional[str] = None
    industry: Optional[str] = None
    price: Optional[float] = None
    marketCap: Optional[float] = None
    dividendYield: Optional[float] = None
    pe_ratio: Optional[float] = Field(None, alias='ttmpe')
    priceToBook: Optional[float] = None
    returns_1y: Optional[float] = Field(None, alias='1YReturns')
    returns_5y: Optional[float] = Field(None, alias='5YReturns')
    volatility: Optional[float] = None

class StockInDB(StockBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    last_updated: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {PyObjectId: str}
        populate_by_name = True
        arbitrary_types_allowed = True

class StockResponse(StockBase):
    id: str = Field(..., alias="_id")
    last_updated: datetime

    class Config:
        json_encoders = {PyObjectId: str}
        populate_by_name = True 