from typing import Literal, Optional

from pydantic import BaseModel, Field


class Visual(BaseModel):
    type: Literal["emoji", "notion_icon"]
    value: str
    color: Optional[str] = None


class RecommendRequest(BaseModel):
    title: str = Field(..., min_length=1)


class RecommendResponse(BaseModel):
    visual: Visual
    reason: str
