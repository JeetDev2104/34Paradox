from pydantic import BaseModel, Field
from typing import Optional, Dict, List
from datetime import datetime
from .base import PyObjectId

class NewsBase(BaseModel):
    title: str
    summary: str
    content: Optional[str] = None
    source: str
    url: str
    date: datetime
    sentiment: str
    sentiment_score: float
    entities: Optional[Dict[str, List[str]]] = Field(default_factory=lambda: {
        "companies": [],
        "sectors": [],
        "locations": []
    })
    keywords: Optional[List[str]] = Field(default_factory=list)

class NewsInDB(NewsBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")

    class Config:
        json_encoders = {PyObjectId: str}
        populate_by_name = True
        arbitrary_types_allowed = True

class NewsResponse(NewsBase):
    id: str = Field(..., alias="_id")

    class Config:
        json_encoders = {PyObjectId: str}
        populate_by_name = True 