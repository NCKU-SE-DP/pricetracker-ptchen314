from datetime import datetime
import json

import itertools
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import delete, insert, select
from sqlalchemy.orm import Session
from typing import List, Optional
from fastapi.responses import JSONResponse
import logging
from fastapi import status
from sqlalchemy.exc import SQLAlchemyError

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
logger = logging.getLogger(__name__)


@router.get("/news", response_model=List[NewsResponse])
def read_news(db: Session = Depends(get_db)):
    """獲取所有新聞"""
    try:
        news = db.query(NewsArticle).order_by(NewsArticle.time.desc()).all()
        result = []
        for article in news:
            upvotes, upvoted = get_article_upvote_details(article.id, None, db)
            article_dict = {
                "id": article.id,
                "title": article.title,
                "content": article.content,
                "time": str(article.time),
                "url": article.link,
                "upvotes": upvotes,
                "is_upvoted": upvoted,
                "summary": article.summary,
                "reason": article.reason
            }
            result.append(article_dict)
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": "success",
                "data": result
            }
        )
    except SQLAlchemyError as db_err:
        logger.error(f"Database error while fetching news: {str(db_err)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "status": "error",
                "message": "資料庫錯誤",
                "detail": str(db_err)
            }
        )
    except Exception as e:
        logger.error(f"Unexpected error while fetching news: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "status": "error",
                "message": "獲取新聞時發生未預期的錯誤",
                "detail": str(e)
            }

        )


@router.get("/user_news", response_model=List[NewsResponse])
def read_user_news(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """獲取用戶相關的新聞"""
    try:
        news = db.query(NewsArticle).order_by(NewsArticle.time.desc()).all()
        result = []
        for article in news:
            upvotes, upvoted = get_article_upvote_details(article.id, current_user.id, db)
            article_dict = {
                "id": article.id,
                "title": article.title,
                "content": article.content,
                "time": str(article.time),
                "link": article.link,
                "upvotes": upvotes,
                "is_upvoted": upvoted
            }
            result.append(article_dict)
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": "success",
                "data": result
            }
        )
    except SQLAlchemyError as db_err:
        logger.error(f"Database error while fetching user news: {str(db_err)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "status": "error",
                "message": "資料庫錯誤",
                "detail": str(db_err)
            }
        )
    except Exception as e:
        logger.error(f"Unexpected error while fetching user news: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "status": "error",
                "message": "獲取用戶新聞時發生未預期的錯誤",
                "detail": str(e)
            }
        )
@router.post("/search_news")
async def search_news(
    request: PromptRequest,
    db: Session = Depends(get_db)
):
    """搜尋新聞"""
    try:
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
                # 檢查新聞是否已存在
                existing_news = db.query(NewsArticle).filter(
                    NewsArticle.link == news["titleLink"]
                ).first()
                
                if existing_news:
                    # 如果新聞已存在，使用現有的新聞
                    article_dict = existing_news.to_dict()
                    news_list.append(article_dict)
                else:
                    # 如果新聞不存在，獲取內容並保存
                    article_content = udn_crawler.get_article_content(news["titleLink"])
                    if article_content:
                        news_article = NewsArticle(
                            title=article_content["title"],
                            content=article_content["content"],
                            time=datetime.strptime(article_content["time"], "%Y-%m-%d %H:%M"),
                            link=news["titleLink"]
                        )
                        db.add(news_article)
                        db.commit()
                        db.refresh(news_article)
                        
                        article_dict = news_article.to_dict()
                        news_list.append(article_dict)
                        
            except Exception as e:
                logger.error(f"Error processing article {news.get('titleLink')}: {str(e)}")
                continue
                
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": "success",
                "data": sorted(news_list, key=lambda x: x["time"], reverse=True)
            }
        )
    except Exception as e:
        logger.error(f"Error in search_news: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "status": "error",
                "message": "搜尋新聞時發生錯誤",
                "detail": str(e)
            }
        )

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
        data = {
            "summary": summary_dict["影響"],
            "reason": summary_dict["原因"]
        }
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": "success",
                "data": data
            }
        )
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
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": "success",
                "data": result
            }
        )
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
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": "success",
                "data": result
            }
        )
    else:
        raise HTTPException(status_code=400, detail="Invalid model name")

