import pytest
from fastapi.testclient import TestClient
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.main import app
from src.models import NewsArticle
from src.database import SessionLocal

client = TestClient(app)

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

def test_get_news(db):
    response = client.get("/api/v1/news/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
