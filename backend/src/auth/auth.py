from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
import logging

from src.models import User
from src.database import get_db
from src.auth.models import authenticate_user, create_access_token, get_password_hash, get_current_user
from src.auth.schemas import UserAuthSchema
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/users", tags=["users"])

@router.post("/login")
async def login_for_access_token(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    try:
        logger.info(f"Login attempt for user: {form_data.username}")
        user = authenticate_user(db, form_data.username, form_data.password)
        if not user:
            logger.warning(f"Failed login attempt for user: {form_data.username}")
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={
                    "status": "error",
                    "message": "帳號或密碼錯誤",
                    "detail": "Invalid credentials"
                }
            )
        
        try:
            access_token = create_access_token(
                data={"sub": user.username},
                expires_delta=timedelta(minutes=30)
            )
        except Exception as token_error:
            logger.error(f"Token generation error: {str(token_error)}")
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "status": "error",
                    "message": "Token 生成失敗",
                    "detail": str(token_error)
                }
            )

        logger.info(f"Successful login for user: {form_data.username}")
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"status": "success",
                    "data":{
                        "access_token": access_token,
                        "token_type": "bearer"
                    }
            }
        )
    except SQLAlchemyError as db_error:
        logger.error(f"Database error during login: {str(db_error)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "status": "error",
                "message": "資料庫錯誤",
                "detail": str(db_error)
            }
        )
    except Exception as e:
        logger.error(f"Login error for user {form_data.username}: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "status": "error",
                "message": "登入過程發生錯誤",
                "detail": str(e)
            }
        )


@router.post("/register")
def create_user(user: UserAuthSchema, db: Session = Depends(get_db)):
    try:
        logger.info(f"Registration attempt for username: {user.username}")
        db_user = db.query(User).filter(User.username == user.username).first()
        if db_user:
            logger.warning(f"Registration failed - username already exists: {user.username}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="使用者名稱已被註冊"
            )
        hashed_password = get_password_hash(user.password)
        db_user = User(username=user.username, hashed_password=hashed_password)
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        logger.info(f"Successfully registered new user: {user.username}")
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"status": "success",
                    "data":{
                        "username": db_user.username
                    }
            }
        )
    except Exception as e:
        logger.error(f"Registration error for {user.username}: {str(e)}")
        raise

@router.get("/me")
def read_users_me(current_user: User = Depends(get_current_user)):
    try:
        logger.info(f"Profile access for user: {current_user.username}")
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"status": "success",
                    "data":{
                        "username": current_user.username
                    }
            }
        )
    except Exception as e:
        logger.error(f"Profile access error for {current_user.username}: {str(e)}")
        raise 

