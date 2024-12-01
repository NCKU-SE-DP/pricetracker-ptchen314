import pytest
from datetime import datetime
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.models import NewsArticle
from src.database import SessionLocal

@pytest.fixture(scope="function")
def db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture(autouse=True)
def clean_db(db):
    db.query(NewsArticle).delete()
    db.commit()
    yield
    db.query(NewsArticle).delete()
    db.commit()

def test_get_news(test_client, db):
    response = test_client.get("/api/v1/news/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_get_news_empty(test_client, db):
    response = test_client.get("/api/v1/news/")
    assert response.status_code == 200
    assert response.json() == []

def test_get_news_with_data(test_client, db):
    news = NewsArticle(
        title="測試新聞",
        url="https://test.com/news/1",
        content="測試內容",
        published_at=datetime.fromisoformat("2024-03-20T10:00:00")
    )
    db.add(news)
    db.commit()

    response = test_client.get("/api/v1/news/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["title"] == "測試新聞"
