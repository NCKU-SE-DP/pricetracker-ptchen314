import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime
import pytest
from bs4 import BeautifulSoup
from pydantic import AnyHttpUrl

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.crawlers.udn_crawler import UDNCrawler
from src.crawlers.base import News, Headline
from src.models import NewsArticle

@pytest.fixture
def crawler():
    return UDNCrawler()

@pytest.fixture
def mock_html():
    return """
    <div class="story-list__news">
        <h2><a href="/news/story/1">測試新聞標題</a></h2>
        <time>2024-03-20 10:00</time>
    </div>
    """

@pytest.fixture
def mock_article_html():
    return """
    <div>
        <h1 class="article-content__title">測試新聞標題</h1>
        <time class="article-content__time">2024-03-20 10:00</time>
        <div class="article-content__editor">這是測試新聞內容</div>
    </div>
    """

@pytest.mark.asyncio
@patch('aiohttp.ClientSession')
async def test_get_headline(mock_session, crawler, mock_html):
    mock_response = MagicMock()
    mock_response.text.return_value = mock_html
    mock_session.return_value.__aenter__.return_value.get.return_value.__aenter__.return_value = mock_response

    headlines = await crawler.get_headline(search_term="", page=1)
    
    assert len(headlines) == 1
    assert headlines[0].title == "測試新聞標題"
    assert headlines[0].url == "https://udn.com/news/story/1"

@pytest.mark.asyncio
@patch('aiohttp.ClientSession')
async def test_parse(mock_session, crawler, mock_article_html):
    mock_response = MagicMock()
    mock_response.text.return_value = mock_article_html
    mock_session.return_value.__aenter__.return_value.get.return_value.__aenter__.return_value = mock_response

    url = "https://udn.com/news/story/1"
    news = await crawler.parse(url)
    
    assert news.title == "測試新聞標題"
    assert news.url == url
    assert news.content == "這是測試新聞內容"
    datetime.fromisoformat(news.time)

def test_save(crawler):
    mock_db = MagicMock()
    test_news = News(
        title="測試新聞標題",
        url="https://udn.com/news/story/1",
        time="2024-03-20T10:00:00",
        content="這是測試新聞內容"
    )
    
    crawler.save(test_news, mock_db)
    
    mock_db.add.assert_called_once()
    mock_db.commit.assert_called_once()
    
    added_article = mock_db.add.call_args[0][0]
    assert isinstance(added_article, NewsArticle)
    assert added_article.title == "測試新聞標題"
    assert added_article.url == "https://udn.com/news/story/1"
    assert added_article.content == "這是測試新聞內容"

def test_is_valid_url_valid(crawler):
    valid_url = "https://udn.com/news/story/1"
    assert crawler._is_valid_url(valid_url) is True

def test_is_valid_url_invalid(crawler):
    invalid_url = "https://example.com/news/1"
    assert crawler._is_valid_url(invalid_url) is False 