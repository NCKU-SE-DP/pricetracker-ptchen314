from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from jose import jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from bs4 import BeautifulSoup
import requests
import json
from openai import OpenAI
from urllib.parse import quote
from sqlalchemy import select, delete, insert

from .models import User, NewsArticle
from .config import settings
from .schemas import UserAuthSchema

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class NewsService:
    @staticmethod
    async def get_news_info(search_term: str, is_initial: bool = False) -> list:
        all_news_data = []
        if is_initial:
            a = []
            for p in range(1, 10):
                p2 = {
                    "page": p,
                    "id": f"search:{quote(search_term)}",
                    "channelId": 2,
                    "type": "searchword",
                }
                response = requests.get("https://udn.com/api/more", params=p2)
                a.append(response.json()["lists"])
            for l in a:
                all_news_data.append(l)
        else:
            p = {
                "page": 1,
                "id": f"search:{quote(search_term)}",
                "channelId": 2,
                "type": "searchword",
            }
            response = requests.get("https://udn.com/api/more", params=p)
            all_news_data = response.json()["lists"]
        return all_news_data

    @staticmethod
    async def add_news(news_data: Dict[str, Any], db: Session):
        news = NewsArticle(
            url=news_data["url"],
            title=news_data["title"],
            time=news_data["time"],
            content=" ".join(news_data["content"]),
            summary=news_data["summary"],
            reason=news_data["reason"],
        )
        db.add(news)
        db.commit()
        db.refresh(news)
        return news

    @staticmethod
    async def get_article_upvote_details(article_id: int, user_id: Optional[int], db: Session) -> tuple[int, bool]:
        from src.models import user_news_association_table
        cnt = db.query(user_news_association_table).filter_by(news_articles_id=article_id).count()
        voted = False
        if user_id:
            voted = (
                db.query(user_news_association_table)
                .filter_by(news_articles_id=article_id, user_id=user_id)
                .first() is not None
            )
        return cnt, voted

    @staticmethod
    async def toggle_upvote(article_id: int, user_id: int, db: Session) -> str:
        from src.models import user_news_association_table
        existing_upvote = db.execute(
            select(user_news_association_table).where(
                user_news_association_table.c.news_articles_id == article_id,
                user_news_association_table.c.user_id == user_id,
            )
        ).scalar()

        if existing_upvote:
            delete_stmt = delete(user_news_association_table).where(
                user_news_association_table.c.news_articles_id == article_id,
                user_news_association_table.c.user_id == user_id,
            )
            db.execute(delete_stmt)
            db.commit()
            return "Upvote removed"
        else:
            insert_stmt = insert(user_news_association_table).values(
                news_articles_id=article_id, user_id=user_id
            )
            db.execute(insert_stmt)
            db.commit()
            return "Article upvoted"

class AIService:
    @staticmethod
    async def generate_summary(content: str) -> dict:
        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        msg = [
            {
                "role": "system",
                "content": "你是一個新聞摘要生成機器人，請統整新聞中提及的影響及主要原因 (影響、原因各50個字，請以json格式回答 {'影響': '...', '原因': '...'})",
            },
            {"role": "user", "content": content},
        ]
        completion = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=msg,
        )
        return json.loads(completion.choices[0].message.content)

    @staticmethod
    async def extract_search_keywords(content: str) -> str:
        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        msg = [
            {
                "role": "system",
                "content": "你是一個關鍵字提取機器人，用戶將會輸入一段文字，表示其希望看見的新聞內容，請提取出用戶希望看見的關鍵字，請截取最重要的關鍵字即可，避免出現「新聞」、「資訊」等混淆搜尋引擎的字詞。(僅須回答關鍵字，若有多個關鍵字，請以空格分隔)",
            },
            {"role": "user", "content": content},
        ]
        completion = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=msg,
        )
        return completion.choices[0].message.content