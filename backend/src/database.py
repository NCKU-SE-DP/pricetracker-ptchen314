from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.exc import SQLAlchemyError, OperationalError, DatabaseError
from fastapi import HTTPException, status
import logging
from src.config import settings

logger = logging.getLogger(__name__)

try:
    engine = create_engine(settings.DATABASE_URL, echo=True)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base = declarative_base()
    logger.info("Database connection established successfully")
except OperationalError as op_err:
    logger.critical(f"Database connection failed - operational error: {str(op_err)}")
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail={
            "status": "error",
            "message": "資料庫連線失敗",
            "detail": str(op_err)
        }
    )
except DatabaseError as db_err:
    logger.critical(f"Database connection failed - database error: {str(db_err)}")
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail={
            "status": "error",
            "message": "資料庫錯誤",
            "detail": str(db_err)
        }
    )
except Exception as e:
    logger.critical(f"Unexpected error during database initialization: {str(e)}")
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail={
            "status": "error",
            "message": "資料庫初始化過程發生未預期的錯誤",
            "detail": str(e)
        }
    )

def get_db():
    db = SessionLocal()
    try:
        yield db
    except OperationalError as op_err:
        logger.error(f"Database session operational error: {str(op_err)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "status": "error",
                "message": "資料庫連線異常",
                "detail": str(op_err)
            }
        )
    except SQLAlchemyError as sql_err:
        logger.error(f"Database session SQLAlchemy error: {str(sql_err)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "status": "error",
                "message": "資料庫操作錯誤",
                "detail": str(sql_err)
            }
        )
    except Exception as e:
        logger.error(f"Unexpected database session error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "status": "error",
                "message": "資料庫連線過程發生未預期的錯誤",
                "detail": str(e)
            }
        )
    finally:
        logger.debug("Closing database session")
        try:
            db.close()
        except Exception as close_err:
            logger.error(f"Error closing database session: {str(close_err)}") 