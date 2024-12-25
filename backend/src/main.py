from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import sentry_sdk
from apscheduler.schedulers.background import BackgroundScheduler
import logging

from src.config import settings
from src.database import engine, Base, SessionLocal
from src.models import NewsArticle
from src.auth.auth import router as auth_router
from src.news.news import router as news_router
from src.prices.prices import router as prices_router
from src.news import news
from src.news.models import get_new

# 設置日誌記錄
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


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

# 錯誤處理器
@app.exception_handler(Exception)
async def bruh_general_exception_handler(request: Request, exc: Exception):
    logger.error(f"General error occurred: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "message": "內部伺服器錯誤",
            "detail": str(exc),
            "path": str(request.url)
        }
    )

@app.exception_handler(ValueError)
async def bruh_value_error_handler(request: Request, exc: ValueError):
    logger.error(f"Value error occurred: {str(exc)}")
    return JSONResponse(
        status_code=400,
        content={
            "status": "error",
            "message": "數值錯誤",
            "detail": str(exc),
            "path": str(request.url)
        }
    )

@app.exception_handler(KeyError)
async def bruh_key_error_handler(request: Request, exc: KeyError):
    logger.error(f"Key error occurred: {str(exc)}")
    return JSONResponse(
        status_code=400,
        content={
            "status": "error",
            "message": "鍵值錯誤",
            "detail": str(exc),
            "path": str(request.url)
        }
    )

@app.exception_handler(TypeError)
async def bruh_type_error_handler(request: Request, exc: TypeError):
    logger.error(f"Type error occurred: {str(exc)}")
    return JSONResponse(
        status_code=400,
        content={
            "status": "error",
            "message": "型別錯誤",
            "detail": str(exc),
            "path": str(request.url)
        }
    )

# Database error handler
from sqlalchemy.exc import SQLAlchemyError
@app.exception_handler(SQLAlchemyError)
async def bruh_database_error_handler(request: Request, exc: SQLAlchemyError):
    logger.error(f"Database error occurred: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "message": "資料庫錯誤",
            "detail": str(exc),
            "path": str(request.url)
        }
    )

# Register routers
app.include_router(auth_router)
app.include_router(news_router)
app.include_router(prices_router)

async def scheduled_news_update():
    db = SessionLocal()
    try:
        logger.info("Starting scheduled news update")
        get_new(db)
        logger.info("Completed scheduled news update")
    except Exception as e:
        logger.error(f"Error in scheduled news update: {str(e)}", exc_info=True)

    finally:
        db.close()

@app.on_event("startup")
async def startup_event():
    logger.info("Application starting up")
    # Initialize news database if empty
    db = SessionLocal()
    try:
        if db.query(NewsArticle).count() == 0:
            logger.info("Initializing news database")
            get_new(db, is_initial=True)
    except Exception as e:
        logger.error(f"Error during startup: {str(e)}", exc_info=True)

    finally:
        db.close()
    
    # Start scheduler
    try:
        scheduler.add_job(scheduled_news_update, "interval", minutes=100)
        scheduler.start()
        logger.info("Scheduler started successfully")
    except Exception as e:
        logger.error(f"Error starting scheduler: {str(e)}", exc_info=True)


@app.on_event("shutdown")
def shutdown_event():
    logger.info("Application shutting down")
    try:
        scheduler.shutdown()
        logger.info("Scheduler shut down successfully")
    except Exception as e:
        logger.error(f"Error during shutdown: {str(e)}", exc_info=True)