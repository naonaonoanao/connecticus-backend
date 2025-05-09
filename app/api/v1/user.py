import traceback
from typing import Dict
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from app.core.config import settings
from app.db.get_db import get_db
from app.models.models import Users, Employers
from app.schemas.schemas import UserCreate, UserResponse, Token, LoginDTO
from app.services.user_service import (
    token_blacklist,
    failed_attempts_cache,
    verify_password,
    get_password_hash,
    create_access_token,
    get_current_user, get_user_with_related
)

router = APIRouter(prefix='/user', tags=['User'])


@router.post("/login", response_model=Token)
def login(data: LoginDTO, db: Session = Depends(get_db)):
    user = db.query(Users).filter(Users.username == data.username).first()
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect username or password")

    cache = failed_attempts_cache.get(data.username, {"attempts": 0, "banned_until": None})
    banned_until = cache.get("banned_until")
    if banned_until and datetime.utcnow() < banned_until:
        raise HTTPException(status_code=403, detail="User is banned. Try again later.")

    if not verify_password(data.password, user.hashed_password):
        attempts = cache.get("attempts", 0) + 1
        banned_until = None
        if attempts >= settings.MAX_FAILED_ATTEMPTS:
            banned_until = datetime.utcnow() + timedelta(minutes=settings.BAN_DURATION_MINUTES)
            attempts = 0
        failed_attempts_cache[data.username] = {"attempts": attempts, "banned_until": banned_until}
        raise HTTPException(status_code=400, detail="Incorrect username or password")

    if data.username in failed_attempts_cache:
        del failed_attempts_cache[data.username]

    token_data = {"sub": user.username}  # TODO: сюда можем дальше подкладывать роль
    access_token = create_access_token(data=token_data)
    return Token(access_token=access_token)


@router.post("/logout")
def logout(user_data: Dict = Depends(get_current_user)):
    token_blacklist.add(user_data['token'])
    return {"msg": "Successfully logged out"}


@router.get("/me", response_model=UserResponse)
def get_me(
    user_data: Dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        username = user_data["user"].username
        user = get_user_with_related(db, username)

        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        return user
    except HTTPException:
        raise
    except Exception:
        traceback.print_exc()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal error")
