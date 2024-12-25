from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
import logging
from src.models import NewsArticle, user_news_association_table
from src.crawler import udn_crawler
import json
import src.llm_client.openai_client as openai_client
from src.config import settings

openai_client = openai_client.create_openai_client(settings.OPENAI_API_KEY)
logger = logging.getLogger(__name__)

def get_new(db: Session, is_initial: bool = False):
    """獲取新聞並寫入資料庫"""
    try:
        # 如果是初始化，搜尋價格相關新聞
        if is_initial:
            news_items = udn_crawler.get_news_list("價格", is_initial=True)
            logger.info(f"Fetched {len(news_items)} news items for regular update")
        else:
            # 一般更新時獲取最新新聞
            news_items = udn_crawler.get_news_list("價格", is_initial=False)
            logger.info(f"Fetched {len(news_items)} news items for regular update")
        
        added_count = 0
        for news in news_items:
            try:
                # 檢查新聞是否已存在
                existing_news = db.query(NewsArticle).filter(
                    NewsArticle.link == news["titleLink"]
                ).first()
                
                if not existing_news:
                    # 獲取文章內容
                    article_content = None
                    if news["titleLink"].startswith("https://udn"):
                        article_content = udn_crawler.get_article_content(news["titleLink"])
                    else:
                        article_content = None
                        break
                    if article_content:
                        # 創建新聞對象
                        summary_result = openai_client.chat_completion(
                            messages=[
                                    {
                                        "role": "system",
                                        "content": "你是一個新聞摘要生成機器人，請統整新聞中提及的影響及主要原因 (影響、原因各50個字，請以json格式回答 {\"影響\": \"...\", \"原因\": \"...\"})",
                                    },
                                    {
                                        "role": "user",
                                        "content": article_content["content"]
                                    }
                                ]
                            )
                        try:
                            if isinstance(summary_result, dict):
                                summary_text = summary_result.get('content', '{}')
                            else:
                                summary_text = str(summary_result)
                                
                            summary_dict = json.loads(summary_text)
                            article_content["summary"] = summary_dict["影響"]
                            article_content["reason"] = summary_dict["原因"]
                        except Exception as e:
                            logger.error(f"Error processing summary: {str(e)}")
                            article_content["summary"] = ""
                            article_content["reason"] = ""
                    
                        news_article = NewsArticle(
                            title=article_content["title"],
                            content=article_content["content"],
                            time=datetime.strptime(article_content["time"], "%Y-%m-%d %H:%M"),
                            link=news["titleLink"],
                            summary=article_content["summary"],
                            reason=article_content["reason"]
                        )
                        
                        db.add(news_article)
                        added_count += 1
                        logger.info(f"Added new article: {news_article.title}")
                
            except Exception as article_error:
                logger.error(f"Error processing article {news.get('titleLink')}: {str(article_error)}")
                continue
        
        if added_count > 0:
            db.commit()
            logger.info(f"Successfully committed {added_count} new articles to database")
        else:
            logger.info("No new articles to add")
        
    except SQLAlchemyError as db_error:
        logger.error(f"Database error while adding news: {str(db_error)}")
        db.rollback()
        raise
    except Exception as e:
        logger.error(f"Unexpected error while getting news: {str(e)}")
        db.rollback()
        raise

def get_article_upvote_details(article_id: int, user_id: int, db: Session):
    """獲取文章的投票詳情"""
    try:
        # 獲取總投票數
        upvotes = db.query(user_news_association_table).filter(
            user_news_association_table.c.news_articles_id == article_id
        ).count()
        
        # 檢查當前用戶是否投票
        if user_id:
            is_upvoted = db.query(user_news_association_table).filter(
                user_news_association_table.c.news_articles_id == article_id,
                user_news_association_table.c.user_id == user_id
            ).first() is not None
        else:
            is_upvoted = False
            
        return upvotes, is_upvoted
        
    except SQLAlchemyError as db_error:
        logger.error(f"Database error while getting upvote details: {str(db_error)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error while getting upvote details: {str(e)}")
        raise
