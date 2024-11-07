import sentry_sdk
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.background import BackgroundScheduler

from src.config import settings
from src.models import Base, NewsArticle
from src.database import engine, SessionLocal
from src.auth import auth
from src.news import news
from src.services import NewsService
from src.prices import prices

# 初始化資料庫
Base.metadata.create_all(bind=engine)

# 初始化 Sentry
sentry_sdk.init(
    dsn=settings.SENTRY_DSN,
    traces_sample_rate=1.0,
    profiles_sample_rate=1.0,
)

# 初始化 FastAPI
app = FastAPI()
bgs = BackgroundScheduler()

# 設定 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 註冊路由
app.include_router(auth.router)
app.include_router(news.router)
app.include_router(prices.router)

# Startup & Shutdown Events
@app.on_event("startup")
async def start_scheduler():
    db = SessionLocal()
    if db.query(NewsArticle).count() == 0:
        await NewsService.get_news_info("價格", is_initial=True)
    db.close()
    bgs.add_job(NewsService.get_news_info, "interval", minutes=100, args=["價格"])
    bgs.start()

@app.on_event("shutdown")
def shutdown_scheduler():
    bgs.shutdown()