from sqlalchemy import Column, ForeignKey, Integer, String, Table, Text, DateTime
from sqlalchemy.orm import relationship
from src.database import Base

user_news_association_table = Table(
    "user_news_upvotes",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id"), primary_key=True),
    Column("news_articles_id", Integer, ForeignKey("news_articles.id"), primary_key=True),
)

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False)
    hashed_password = Column(String(200), nullable=False)
    upvoted_news = relationship(
        "NewsArticle",
        secondary=user_news_association_table,
        back_populates="upvoted_by_users",
    )

class NewsArticle(Base):
    __tablename__ = "news_articles"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    content = Column(String)
    time = Column(DateTime)
    link = Column(String)
    summary = Column(Text)
    reason = Column(Text)

    def to_dict(self):
        """將模型轉換為可序列化的字典"""
        return {
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "time": self.time.isoformat() if self.time else None,
            "link": self.link,
            "summary": self.summary,
            "reason": self.reason
        }

    upvoted_by_users = relationship(
        "User", 
        secondary=user_news_association_table, 
        back_populates="upvoted_news"
    ) 