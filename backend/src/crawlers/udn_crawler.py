import aiohttp
from bs4 import BeautifulSoup
from datetime import datetime
from typing import List
from sqlalchemy.orm import Session
from pydantic import AnyHttpUrl

from models import NewsArticle
from base import NewsCrawlerBase, News, Headline

async def get_news_list(search_term: str = "", page: int = 1) -> List[Headline]:
    """獲取聯合新聞網的新聞列表"""
    url = f"https://udn.com/news/cate/2/6644"
    if search_term:
        url = f"https://udn.com/search/word/2/{search_term}"
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            html = await response.text()
            
    soup = BeautifulSoup(html, 'html.parser')
    news_items = soup.select('div.story-list__news')
    
    headlines = []
    for item in news_items:
        headline = Headline(
            title=item.select_one('h2').text.strip(),
            url=f"https://udn.com{item.select_one('a')['href']}"
        )
        headlines.append(headline)
    
    return headlines

async def get_news_content(url: AnyHttpUrl | str) -> News:
    """獲取單篇新聞內容"""
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            html = await response.text()
            
    soup = BeautifulSoup(html, 'html.parser')
    content = soup.select_one('div.article-content__editor')
    title = soup.select_one('h1.article-content__title').text.strip()
    time = soup.select_one('time.article-content__time').text.strip()
    
    return News(
        title=title,
        url=url,
        time=_parse_date(time).isoformat(),
        content=content.text.strip() if content else ''
    )

def save_news(news: News, db: Session):
    """儲存新聞到資料庫"""
    news_article = NewsArticle(
        title=news.title,
        url=str(news.url),
        content=news.content,
        published_at=datetime.fromisoformat(news.time)
    )
    db.add(news_article)
    db.commit()

def _parse_date(date_str: str) -> datetime:
    """解析新聞日期字串"""
    return datetime.strptime(date_str, '%Y-%m-%d %H:%M')

class UDNCrawler(NewsCrawlerBase):
    news_website_url = "https://udn.com"
    news_website_news_child_urls = [
        "https://udn.com/news/cate/2/6644"
    ]

    async def get_headline(
            self, search_term: str, page: int | tuple[int, int]
    ) -> list[Headline]:
        if isinstance(page, tuple):
            page = page[0]  # 暫時只處理第一頁
        return await get_news_list(search_term, page)

    async def parse(self, url: AnyHttpUrl | str) -> News:
        return await get_news_content(url)

    @staticmethod
    def save(news: News, db: Session | None):
        if db:
            save_news(news, db) 