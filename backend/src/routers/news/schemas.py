from pydantic import BaseModel, Field
from typing import Optional, List


class NewsSumaryRequestSchema(BaseModel):
    content: str

class PromptRequest(BaseModel):
    prompt: str


class NewsResponse(BaseModel):
    id: int
    url: str
    title: str
    time: str
    content: str
    summary: str
    reason: str
    upvotes: int
    is_upvoted: bool

    class Config:
        from_attributes = True

class NewsSearchResponse(BaseModel):
    id: int
    url: str
    title: str
    time: str
    content: str

    class Config:
        from_attributes = True

class NewsSummaryResponse(BaseModel):
    summary: str
    reason: str

class UpvoteResponse(BaseModel):
    message: str

class UserAuthSchema(BaseModel):
    username: str
    password: str
