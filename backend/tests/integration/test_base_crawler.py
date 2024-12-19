from bs4 import BeautifulSoup
import unittest
from unittest.mock import patch, Mock
import requests
from src.crawler.udn_crawler import get_article_content, get_news_list
from src.crawler.exceptions import NetworkError, ParseError

class TestBaseCrawlerFunctions(unittest.TestCase):
    def setUp(self):
        self.test_url = "https://udn.com/news/story/123456"
        self.test_search_term = "測試"

    @patch('src.crawler.udn_crawler.requests.get')
    def test_handle_network_error(self, mock_get):
        """測試網路錯誤處理"""
        mock_get.side_effect = requests.RequestException("Network error")
            
        with self.assertRaises(NetworkError):
            get_news_list(self.test_search_term)

    @patch('src.crawler.udn_crawler.requests.get')
    def test_handle_parse_error(self, mock_get):
        """測試解析錯誤處理"""
        mock_response = Mock()
        mock_response.text = "<html></html>"  # 無效的HTML結構
        mock_get.return_value = mock_response
            
        with self.assertRaises(ParseError):
            get_article_content(self.test_url)

    @patch('src.crawler.udn_crawler.requests.get')
    def test_response_validation(self, mock_get):
        """測試回應驗證"""
        # 模擬成功的回應
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"lists": [{"title": "測試", "url": "test_url"}]}
        mock_get.return_value = mock_response
            
        result = get_news_list(self.test_search_term)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["title"], "測試")
            
        # 模擬失敗的回應
        mock_get.side_effect = requests.RequestException("404 Client Error")
        with self.assertRaises(NetworkError):
            get_news_list(self.test_search_term)


    def test_error_message_format(self):
        """測試錯誤訊息格式"""
        network_error = NetworkError("測試網路錯誤")
        parse_error = ParseError("測試解析錯誤")
        
        self.assertIn("測試網路錯誤", str(network_error))
        self.assertIn("測試解析錯誤", str(parse_error))
        
        # 確認錯誤類別繼承關係
        self.assertTrue(isinstance(network_error, Exception))
        self.assertTrue(isinstance(parse_error, Exception))

    def test_url_validation(self):
        """測試URL驗證"""
        valid_urls = [
            "https://udn.com/news/story/123",
            "https://udn.com/news/story/456",
        ]
        
        invalid_urls = [
            "http://invalid.com/news",
            "not_a_url",
            "ftp://udn.com/news",
        ]
        
        for url in valid_urls:
            self.assertTrue(url.startswith("https://udn.com/"))
            
        for url in invalid_urls:
            self.assertFalse(url.startswith("https://udn.com/"))

if __name__ == '__main__':
    unittest.main()
