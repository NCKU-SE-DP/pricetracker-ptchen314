import pytest
from fastapi import APIRouter
import sys
import os

# 添加專案根目錄到 Python 路徑
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 創建 mock routers
mock_auth_router = APIRouter()
mock_news_router = APIRouter()
mock_prices_router = APIRouter()

# 替換模組
sys.modules['auth'] = type('auth', (), {'routes': mock_auth_router})()
sys.modules['news'] = type('news', (), {'routes': mock_news_router})()
sys.modules['prices'] = type('prices', (), {'routes': mock_prices_router})()

@pytest.fixture
def test_app():
    from src.main import app
    return app

@pytest.fixture
def test_client(test_app):
    from fastapi.testclient import TestClient
    return TestClient(test_app) 