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
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="帳號或密碼錯誤",
                headers={"WWW-Authenticate": "Bearer"},
            )
        access_token = create_access_token(
            data={"sub": user.username},
            expires_delta=timedelta(minutes=30)
        )
        logger.info(f"Successful login for user: {form_data.username}")
        return {"access_token": access_token, "token_type": "bearer"}
    except Exception as e:
        logger.error(f"Login error for user {form_data.username}: {str(e)}")
        raise

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
        return db_user
    except Exception as e:
        logger.error(f"Registration error for {user.username}: {str(e)}")
        raise

@router.get("/me")
def read_users_me(current_user: User = Depends(get_current_user)):
    try:
        logger.info(f"Profile access for user: {current_user.username}")
        return {"username": current_user.username}
    except Exception as e:
        logger.error(f"Profile access error for {current_user.username}: {str(e)}")
        raise 