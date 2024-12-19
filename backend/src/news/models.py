import json
from sqlalchemy.orm import Session
from typing import Optional

from src.models import NewsArticle, user_news_association_table, User
from src.crawler import udn_crawler
import src.llm_client.openai_client as openai_client
from src.config import settings

ai_client = openai_client.create_openai_client(settings.OPENAI_API_KEY)

def get_new(db: Session, is_initial: bool = False):
    
    """定期獲取新聞"""
    try:
        if is_initial:
            news_data = get_new_info("價格", is_initial=True)
        else:
            news_data = get_new_info("價格", is_initial=False)
        
        for news in news_data:
            print(news)
            try:
                title = news["title"]
                relevance_response =ai_client.chat_completion(
                    messages=[
                        {
                            "role": "system",
                            "content": "你是一個關聯度評估機器人，請評估新聞標題是否與「民生用品的價格變化」相關，並給予'high'、'medium'、'low'評價。(僅需回答'high'、'medium'、'low'三個詞之一)",
                        },
                        {
                            "role": "user",
                            "content": title
                        }
                    ]
                )
                
                if isinstance(relevance_response, dict):
                    relevance = relevance_response.get('content', '').lower().strip()
                else:
                    relevance = str(relevance_response).lower().strip()
                
                if relevance == "high":
                    try:
                        article_content = udn_crawler.get_article_content(news["titleLink"])
                        if article_content:
                            summary_result = ai_client.chat_completion(
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
                                add_new_article(article_content, db)
                            except json.JSONDecodeError:
                                print(f"Failed to parse summary JSON for article: {title}")
                                continue
                    except Exception as e:
                        print(f"Failed to get article content for {title}: {str(e)}")
                        continue
            except Exception as e:
                print(f"Error processing news item: {str(e)}")
                continue
    except Exception as e:
        print(f"Error in get_new: {str(e)}")

def get_new_info(search_term: str, is_initial: bool = False):
    """從UDN獲取新聞列表"""
    return udn_crawler.get_news_list(search_term, is_initial)

def add_new_article(news_data: dict, db: Session):
    """添加新聞到資料庫"""
    article = NewsArticle(
        url=news_data["url"],
        title=news_data["title"],
        time=news_data["time"],
        content=news_data["content"],
        summary=news_data.get("summary"),
        reason=news_data.get("reason"),
    )
    db.add(article)
    db.commit()
    return article

def get_article_upvote_details(article_id: int, user_id: Optional[int], db: Session):
    """獲取文章的投票詳情"""
    count = db.query(user_news_association_table).filter_by(news_articles_id=article_id).count()
    voted = False
    if user_id:
        voted = (
            db.query(user_news_association_table)
            .filter_by(news_articles_id=article_id, user_id=user_id)
            .first() is not None
        )
    return count, voted
