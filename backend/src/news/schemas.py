from pydantic import BaseModel
from typing import Optional

class NewsResponse(BaseModel):
    id: int
    url: str
    title: str
    time: str
    content: str
    summary: Optional[str]
    reason: Optional[str]
    upvotes: int
    is_upvoted: bool

class PromptRequest(BaseModel):
    prompt: str

class NewsSummaryRequest(BaseModel):
    content: str
