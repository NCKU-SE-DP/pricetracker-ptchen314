import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime
from bs4 import BeautifulSoup
from pydantic import AnyHttpUrl

from src.crawlers.udn_crawler import UDNCrawler
from src.crawlers.base import News, Headline
from src.models import NewsArticle

class TestUDNCrawler(unittest.TestCase):
    def setUp(self):
        self.crawler = UDNCrawler()
        self.mock_html = """
        <div class="story-list__news">
            <h2><a href="/news/story/1">測試新聞標題</a></h2>
            <time>2024-03-20 10:00</time>
        </div>
        """
        self.mock_article_html = """
        <div>
            <h1 class="article-content__title">測試新聞標題</h1>
            <time class="article-content__time">2024-03-20 10:00</time>
            <div class="article-content__editor">這是測試新聞內容</div>
        </div>
        """

    @patch('aiohttp.ClientSession')
    async def test_get_headline(self, mock_session):
        # 設置 mock response
        mock_response = MagicMock()
        mock_response.text = self.mock_html
        mock_session.return_value.__aenter__.return_value.get.return_value.__aenter__.return_value = mock_response

        headlines = await self.crawler.get_headline(search_term="", page=1)
        
        self.assertEqual(len(headlines), 1)
        self.assertEqual(headlines[0].title, "測試新聞標題")
        self.assertEqual(headlines[0].url, "https://udn.com/news/story/1")

    @patch('aiohttp.ClientSession')
    async def test_parse(self, mock_session):
        # 設置 mock response
        mock_response = MagicMock()
        mock_response.text = self.mock_article_html
        mock_session.return_value.__aenter__.return_value.get.return_value.__aenter__.return_value = mock_response

        url = "https://udn.com/news/story/1"
        news = await self.crawler.parse(url)
        
        self.assertEqual(news.title, "測試新聞標題")
        self.assertEqual(news.url, url)
        self.assertEqual(news.content, "這是測試新聞內容")
        
        # 檢查時間格式是否正確
        datetime.fromisoformat(news.time)  # 如果格式不正確會拋出異常

    def test_save(self):
        # 創建 mock Session
        mock_db = MagicMock()
        
        # 創建測試新聞
        test_news = News(
            title="測試新聞標題",
            url="https://udn.com/news/story/1",
            time="2024-03-20T10:00:00",
            content="這是測試新聞內容"
        )
        
        # 執行儲存
        self.crawler.save(test_news, mock_db)
        
        # 驗證是否正確呼叫了 add 和 commit
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        
        # 驗證傳入 add 的參數是否正確
        added_article = mock_db.add.call_args[0][0]
        self.assertIsInstance(added_article, NewsArticle)
        self.assertEqual(added_article.title, "測試新聞標題")
        self.assertEqual(added_article.url, "https://udn.com/news/story/1")
        self.assertEqual(added_article.content, "這是測試新聞內容")

    def test_is_valid_url_valid(self):
        valid_url = "https://udn.com/news/story/1"
        self.assertTrue(self.crawler._is_valid_url(valid_url))

    def test_is_valid_url_invalid(self):
        invalid_url = "https://example.com/news/1"
        self.assertFalse(self.crawler._is_valid_url(invalid_url))

if __name__ == '__main__':
    unittest.main() 