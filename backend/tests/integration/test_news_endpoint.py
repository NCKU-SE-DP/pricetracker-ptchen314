import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.main import app
from src.models import NewsArticle
from src.database import SessionLocal

client = TestClient(app)

@pytest.fixture
def db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture(autouse=True)
def clean_db(db: Session):
    """Clean database before and after each test"""
    db.query(NewsArticle).delete()
    db.commit()
    yield
    db.query(NewsArticle).delete()
    db.commit()

def test_get_news(db: Session):
    """Test getting news list endpoint"""
    response = client.get("/api/v1/news/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
