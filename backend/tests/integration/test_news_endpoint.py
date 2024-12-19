import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, StaticPool
from sqlalchemy.orm import sessionmaker
import json
from jose import jwt
from src.main import app
from src.models import Base, NewsArticle, User, user_news_association_table
from src.database import get_db
from src.news.schemas import NewsSummaryRequest, PromptRequest
from src.auth.models import pwd_context
from unittest.mock import Mock
import sys
import os

# 添加測試配置到 Python 路徑
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from config import settings

SECRET_KEY = "1892dhianiandowqd0n"
ALGORITHM = "HS256"
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}, poolclass=StaticPool)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

@pytest.fixture(scope="module")
def clear_users():
    with next(override_get_db()) as db:
        db.query(User).delete()
        db.commit()

@pytest.fixture(scope="module")
def test_user(clear_users):
    hashed_password = pwd_context.hash("testpassword")

    with next(override_get_db()) as db:
        user = User(username="testuser", hashed_password=hashed_password)
        db.add(user)
        db.commit()
        db.refresh(user)
        return user


@pytest.fixture(scope="module")
def test_token(test_user):
    access_token = jwt.encode({"sub": test_user.username}, SECRET_KEY, algorithm=ALGORITHM)
    return access_token


@pytest.fixture(scope="module")
def test_articles():
    with next(override_get_db()) as db:
        article_1 = NewsArticle(
            url="https://example.com/test-news-1",
            title="Test News 1",
            content="This is test content 1",
            time="2024-01-01",
            summary="Test summary 1",
            reason="Test reason 1"
        )
        article_2 = NewsArticle(
            url="https://example.com/test-news-2",
            title="Test News 2",
            content="This is test content 2",
            time="2024-01-02",
            summary="Test summary 2",
            reason="Test reason 2"
        )
        db.add_all([article_1, article_2])
        db.commit()
        db.refresh(article_1)
        db.refresh(article_2)

        return [article_1, article_2]


@pytest.fixture(scope="module")
def test_user_and_articles(test_user, test_articles):
    return test_user, test_articles


def test_read_news(test_articles):
    response = client.get("/api/v1/news/news")
    assert response.status_code == 200
    json_response = response.json()
    assert len(json_response) == 2
    assert json_response[0]["title"] == "Test News 2"
    assert json_response[1]["title"] == "Test News 1"


def test_read_user_news(test_user, test_token, test_articles):
    headers = {"Authorization": f"Bearer {test_token}"}
    response = client.get("/api/v1/news/user_news", headers=headers)
    print(test_token)
    print(response.json())
    assert response.status_code == 200
    json_response = response.json()
    assert len(json_response) == 2
    assert json_response[0]["title"] == "Test News 2"
    assert json_response[0]["is_upvoted"] is False
    assert json_response[1]["title"] == "Test News 1"
    assert json_response[1]["is_upvoted"] is False

def mock_openai(mocker, return_content):
    mock_openai_client = mocker.patch('src.news.news.openai_client')
    mock_openai_client.chat_completion.return_value = {
        "content": return_content,
        "role": "assistant"
    }
    return mock_openai_client

def test_search_news(mocker):
    # 模擬新聞爬蟲的回應
    mock_get_new_info = mocker.patch("src.crawler.udn_crawler.get_news_list", return_value=[
        {"title": "Test Title", "titleLink": "http://example.com/news1"}
    ])
    
    mock_get = mocker.patch("src.crawler.udn_crawler.get_article_content", return_value={
        "title": "Test Title",
        "time": "2024-09-10",
        "content": "This is a test paragraph."
    })

    response = client.post("/api/v1/news/search_news", json={"prompt": "Test search prompt"})
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["title"] == "Test Title"
    assert data[0]["time"] == "2024-09-10"
    assert data[0]["content"] == "This is a test paragraph."


def test_news_summary(test_token):
    headers = {"Authorization": f"Bearer {test_token}"}
    test_content = "這是一篇測試新聞內容，主要討論AI發展對社會的影響。"
    
    request_body = NewsSummaryRequest(content=test_content)
    response = client.post("/api/v1/news/news_summary", 
                          json=request_body.dict(), 
                          headers=headers)

    assert response.status_code == 200
    json_response = response.json()
    assert "summary" in json_response
    assert "reason" in json_response
    assert isinstance(json_response["summary"], str)
    assert isinstance(json_response["reason"], str)


def test_upvote_article(test_user_and_articles, test_token):
    user, articles = test_user_and_articles
    headers = {"Authorization": f"Bearer {test_token}"}

    response = client.post(f"/api/v1/news/{articles[0].id}/upvote", headers=headers)
    assert response.status_code == 200
    assert response.json()["message"] == "Article upvoted"


def test_downvote_article(test_user_and_articles, test_token):
    user, articles = test_user_and_articles
    headers = {"Authorization": f"Bearer {test_token}"}

    response = client.post(f"/api/v1/news/{articles[0].id}/upvote", headers=headers)
    assert response.status_code == 200
    assert response.json()["message"] == "Upvote removed"
