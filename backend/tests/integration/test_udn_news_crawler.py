import unittest
import requests
from unittest.mock import patch, Mock
from src.crawler import udn_crawler
from src.crawler.exceptions import ParseError, NetworkError

class TestUDNCrawler(unittest.TestCase):
    
    def setUp(self):
        self.test_url = "https://udn.com/news/story/123456"
        self.test_search_term = "測試"
        
    @patch('src.crawler.udn_crawler.requests.get')
    def test_get_news_list_success(self, mock_get):
        # 模擬成功的回應
        mock_response = Mock()
        mock_response.json.return_value = {
            "lists": [
                {
                    "title": "測試新聞1",
                    "url": "https://udn.com/news/story/1"
                }
            ]
        }
        mock_get.return_value = mock_response
        
        result = udn_crawler.get_news_list(self.test_search_term)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["title"], "測試新聞1")
        
    @patch('src.crawler.udn_crawler.requests.get')
    def test_get_news_list_network_error(self, mock_get):
        # 模擬網路錯誤
        mock_get.side_effect = requests.RequestException()
        
        with self.assertRaises(NetworkError):
            udn_crawler.get_news_list(self.test_search_term)
            
    @patch('src.crawler.udn_crawler.requests.get')
    def test_get_news_list_parse_error(self, mock_get):
        # 模擬解析錯誤
        mock_response = Mock()
        mock_response.json.return_value = {}  # 缺少 lists 鍵
        mock_get.return_value = mock_response
        
        with self.assertRaises(ParseError):
            udn_crawler.get_news_list(self.test_search_term)
            
    @patch('src.crawler.udn_crawler.requests.get')
    def test_get_article_content_success(self, mock_get):
        mock_response = Mock()
        mock_response.text = """
        <html>
            <h1 class="article-content__title">測試標題</h1>
            <time class="article-content__time">2024-01-01 12:00</time>
            <section class="article-content__editor">
                <p>段落1</p>
                <p>段落2</p>
            </section>
        </html>
        """
        mock_get.return_value = mock_response
        
        result = udn_crawler.get_article_content(self.test_url)
        
        assert result["title"] == "測試標題"
        assert result["time"] == "2024-01-01 12:00"
        assert result["content"] == "段落1 段落2"
        
    @patch('src.crawler.udn_crawler.requests.get')
    def test_get_article_content_network_error(self, mock_get):
        # 模擬網路錯誤
        mock_get.side_effect = requests.RequestException()
        
        with self.assertRaises(NetworkError):
            udn_crawler.get_article_content(self.test_url)
            
    @patch('src.crawler.udn_crawler.requests.get')
    def test_get_article_content_parse_error(self, mock_get):
        # 模擬缺少必要元素的HTML
        mock_response = Mock()
        mock_response.text = "<html></html>"
        mock_get.return_value = mock_response
        
        with self.assertRaises(ParseError):
            udn_crawler.get_article_content(self.test_url)
            
    @patch('src.crawler.udn_crawler.requests.get')
    def test_get_news_list_initial_load(self, mock_get):
        # 測試初始載入（多頁）
        mock_response = Mock()
        mock_response.json.return_value = {
            "lists": [{"title": f"新聞{i}", "url": f"https://udn.com/news/story/{i}"} for i in range(5)]
        }
        mock_get.return_value = mock_response
        
        result = udn_crawler.get_news_list(self.test_search_term, is_initial=True)
        # 因為 is_initial=True 會呼叫多次 API，所以確認 mock_get 被呼叫的次數
        self.assertTrue(mock_get.call_count > 1)

if __name__ == '__main__':
    unittest.main()
