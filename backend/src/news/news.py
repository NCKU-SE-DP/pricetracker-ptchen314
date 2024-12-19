from datetime import datetime
import json

import itertools
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import delete, insert, select
from sqlalchemy.orm import Session
from typing import List, Optional



from src.models import NewsArticle, user_news_association_table, User
from src.news.models import get_article_upvote_details
from src.news.schemas import NewsResponse, PromptRequest, NewsSummaryRequest
from src.database import get_db
from src.auth.auth import get_current_user
from src.config import settings
from src.crawler import udn_crawler
import src.llm_client.openai_client as openai_client
import src.llm_client.anthropic_client as anthropic_client
openai_client = openai_client.create_openai_client(settings.OPENAI_API_KEY)
anthropic_client = anthropic_client.create_anthropic_client(settings.ANTHROPIC_API_KEY)
router = APIRouter(prefix="/api/v1/news", tags=["news"])
_id_counter = itertools.count(start=1000000)


@router.get("/news", response_model=List[NewsResponse])
def read_news(db: Session = Depends(get_db)):
    """獲取所有新聞"""
    news = db.query(NewsArticle).order_by(NewsArticle.time.desc()).all()
    result = []
    for article in news:
        upvotes, upvoted = get_article_upvote_details(article.id, None, db)
        article_dict = {
            **article.__dict__,
            "upvotes": upvotes,
            "is_upvoted": upvoted
        }
        result.append(article_dict)
    return result

@router.get("/user_news", response_model=List[NewsResponse])
def read_user_news(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """獲取用戶相關的新聞"""
    news = db.query(NewsArticle).order_by(NewsArticle.time.desc()).all()
    result = []
    for article in news:
        upvotes, upvoted = get_article_upvote_details(article.id, current_user.id, db)
        article_dict = {
            **article.__dict__,
            "upvotes": upvotes,
            "is_upvoted": upvoted
        }
        result.append(article_dict)
    return result
@router.post("/search_news")
async def search_news(
    request: PromptRequest,
    db: Session = Depends(get_db)
):
    """搜尋新聞"""
    response = openai_client.chat_completion(
        messages=[
            {
                "role": "system", 
                "content": "你是一個關鍵字提取機器人，用戶將會輸入一段文字，表示其希望看見的新聞內容，請提取出用戶希望看見的關鍵字，請截取最重要的關鍵字即可，避免出現「新聞」、「資訊」等混淆搜尋引擎的字詞。(僅須回答關鍵字，且只需一個關鍵字)",
            },
            {
                "role": "user",
                "content": request.prompt
            }
        ]
    )
    keywords = response["content"]
    
    news_list = []
    news_items = udn_crawler.get_news_list(str(keywords), is_initial=False)
    
    for news in news_items:
        try:
            article_content = udn_crawler.get_article_content(news["titleLink"])
            if article_content:
                article_content["id"] = next(_id_counter)
                news_list.append(article_content)
        except Exception as e:
            continue
            
    return sorted(news_list, key=lambda x: x["time"], reverse=True)

@router.post("/news_summary")
def news_summary(
    request: NewsSummaryRequest,
    current_user: User = Depends(get_current_user)
):
    """生成新聞摘要"""
    result = openai_client.chat_completion(
        messages=[
            {
                "role": "system",
                "content": "你是一個新聞摘要生成機器人，請統整新聞中提及的影響及主要原因 (影響、原因各50個字，請以json格式回答 {\"影響\": \"...\", \"原因\": \"...\"})",
            },
            {
                "role": "user",
                "content": request.content
            }
        ]
    )
    
    try:
        summary_dict = json.loads(result.get("content", "{}"))
        return {
            "summary": summary_dict["影響"],
            "reason": summary_dict["原因"]
        }
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Failed to generate summary")

@router.post("/{id}/upvote")
def upvote_article(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """投票/取消投票文章"""
    article = db.query(NewsArticle).filter(NewsArticle.id == id).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
        
    existing_upvote = db.execute(
        select(user_news_association_table).where(
            user_news_association_table.c.news_articles_id == id,
            user_news_association_table.c.user_id == current_user.id,
        )
    ).scalar()

    if existing_upvote:
        delete_stmt = delete(user_news_association_table).where(
            user_news_association_table.c.news_articles_id == id,
            user_news_association_table.c.user_id == current_user.id,
        )
        db.execute(delete_stmt)
        db.commit()
        return {"message": "Upvote removed"}
    else:
        insert_stmt = insert(user_news_association_table).values(
            news_articles_id=id,
            user_id=current_user.id
        )
        db.execute(insert_stmt)
        db.commit()
        return {"message": "Article upvoted"} 
    

@router.post("/news_summary_custom_model")
def news_summary_custom_model(
    request: NewsSummaryRequest,
    db: Session = Depends(get_db),
    model_name: str = "openai",
    current_user: User = Depends(get_current_user)
):
    """使用自定義模型生成新聞摘要"""
    if model_name == "openai":
        result = openai_client.chat_completion(
            messages=[
                {
                    "role": "system",
                    "content": "你是一個新聞摘要生成機器人，請統整新聞中提及的影響及主要原因 (影響、原因各50個字，請以json格式回答 {\"影響\": \"...\", \"原因\": \"...\"})",
                },
                {
                    "role": "user",
                    "content": request.content
                }
            ]
        )
        result = json.loads(result["content"])
        return result
    elif model_name == "claude":
        result = anthropic_client.chat_completion(
            messages=[
                {
                    "role": "system",
                    "content": "你是一個新聞摘要生成機器人，請統整新聞中提及的影響及主要原因 (影響、原因各50個字，無論有無回復，都請以json格式回答 {\"影響\": \"...\", \"原因\": \"...\"})",
                },
                {
                    "role": "user",
                    "content": request.content
                }
            ]
        )
        print(result)
        result = json.loads(result["content"])
        return result
    else:
        raise HTTPException(status_code=400, detail="Invalid model name")

