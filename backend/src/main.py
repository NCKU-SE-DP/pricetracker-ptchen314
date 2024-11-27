from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import sentry_sdk
from apscheduler.schedulers.background import BackgroundScheduler
from .config import settings
from .database import engine, Base, SessionLocal
from .models import NewsArticle
from auth import routes as auth_router
from news import routes as news_router
from prices import routes as prices_router
from news import news
from crawlers.udn_crawler import UDNCrawler

# Initialize database
Base.metadata.create_all(bind=engine)

# Initialize Sentry
sentry_sdk.init(
    dsn=settings.SENTRY_DSN,
    traces_sample_rate=1.0,
    profiles_sample_rate=1.0,
)

app = FastAPI()
scheduler = BackgroundScheduler()

# Setup CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(auth_router, prefix="/api/v1/users", tags=["users"])
app.include_router(news_router, prefix="/api/v1/news", tags=["news"])
app.include_router(prices_router, prefix="/api/v1/prices", tags=["prices"])

@app.on_event("startup")
async def startup_event():
    # Initialize news database if empty
    db = SessionLocal()
    if db.query(NewsArticle).count() == 0:
        crawler = UDNCrawler()
        headlines = await crawler.get_headline("", 1)
        for headline in headlines:
            news = await crawler.validate_and_parse(headline.url)
            crawler.save(news, db)
    db.close()
    
    # Start scheduler
    scheduler.add_job(startup_event, "interval", minutes=100)
    scheduler.start()

@app.on_event("shutdown")
def shutdown_event():
    scheduler.shutdown() 