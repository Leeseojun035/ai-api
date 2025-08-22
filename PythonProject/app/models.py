from pydantic import BaseModel
from typing import List

class RecommendRequest(BaseModel):
    origin: List[float]       # [lat, lng]
    destination: List[float]
    limit: int = 5
    preferences: str = "tourist"
