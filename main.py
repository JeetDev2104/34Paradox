from typing import Optional
from pydantic import BaseModel

class ChatQuery(BaseModel):
    query: str
    user_id: Optional[str] = "default" 