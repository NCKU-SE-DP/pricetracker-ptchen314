from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import itertools
import requests
from bs4 import BeautifulSoup

from .dependencies import get_db, get_current_user
from .models import User, NewsArticle
from .services import NewsService, AIService
from .schemas import (
    NewsResponse,
    NewsSearchResponse,
    NewsSumaryRequestSchema,
    NewsSummaryResponse,
    PromptRequest,
    UpvoteResponse
)

router = APIRouter(
    prefix="/api/v1/news",
    tags=["News"]
)

@router.get("/news", response_model=List[NewsResponse])
async def read_news(db: Session = Depends(get_db)):
    news = db.query(NewsArticle).order_by(NewsArticle.time.desc()).all()
    result = []
    for n in news:
        upvotes, upvoted = await NewsService.get_article_upvote_details(n.id, None, db)
        result.append({**n.__dict__, "upvotes": upvotes, "is_upvoted": upvoted})
    return result

@router.get("/user_news", response_model=List[NewsResponse])
async def read_user_news(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    news = db.query(NewsArticle).order_by(NewsArticle.time.desc()).all()
    result = []
    for article in news:
        upvotes, upvoted = await NewsService.get_article_upvote_details(article.id, current_user.id, db)
        result.append({**article.__dict__, "upvotes": upvotes, "is_upvoted": upvoted})
    return result

@router.post("/search_news", response_model=List[NewsSearchResponse])
async def search_news(request: PromptRequest):
    keywords = await AIService.extract_search_keywords(request.prompt)
    news_items = await NewsService.get_news_info(keywords, is_initial=False)
    news_list = []
    _id_counter = itertools.count(start=1000000)
    
    for news in news_items:
        try:
            response = requests.get(news["titleLink"])
            soup = BeautifulSoup(response.text, "html.parser")
            title = soup.find("h1", class_="article-content__title").text
            time = soup.find("time", class_="article-content__time").text
            content_section = soup.find("section", class_="article-content__editor")
            paragraphs = [
                p.text
                for p in content_section.find_all("p")
                if p.text.strip() != "" and "▪" not in p.text
            ]
            detailed_news = {
                "url": news["titleLink"],
                "title": title,
                "time": time,
                "content": " ".join(paragraphs),
                "id": next(_id_counter)
            }
            news_list.append(detailed_news)
        except Exception as e:
            print(e)
    return sorted(news_list, key=lambda x: x["time"], reverse=True)

@router.post("/news_summary", response_model=NewsSummaryResponse)
async def news_summary(
    payload: NewsSumaryRequestSchema,
    current_user: User = Depends(get_current_user)
):
    result = await AIService.generate_summary(payload.content)
    return {
        "summary": result["影響"],
        "reason": result["原因"]
    }

@router.post("/{id}/upvote", response_model=UpvoteResponse)
async def upvote_article(
    id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    message = await NewsService.toggle_upvote(id, current_user.id, db)
    return {"message": message}
