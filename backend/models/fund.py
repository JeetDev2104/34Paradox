from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from .base import PyObjectId

class FundBase(BaseModel):
    scheme_name: str
    nav: Optional[float] = None
    aum: Optional[float] = None
    expense_ratio: Optional[float] = None
    fund_category: Optional[str] = None
    fund_type: Optional[str] = None
    fund_house: Optional[str] = None
    risk_level: Optional[str] = None
    returns_1y: Optional[float] = None
    returns_3y: Optional[float] = None
    returns_5y: Optional[float] = None

class FundHolding(BaseModel):
    stock_name: str
    percentage: float
    sector: Optional[str] = None

class FundInDB(FundBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    holdings: List[FundHolding] = []
    last_updated: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {PyObjectId: str}
        populate_by_name = True
        arbitrary_types_allowed = True

class FundResponse(FundBase):
    id: str = Field(..., alias="_id")
    holdings: List[FundHolding] = []
    last_updated: datetime

    class Config:
        json_encoders = {PyObjectId: str}
        populate_by_name = True 