from typing import Dict
from fastapi import APIRouter, Depends, HTTPException
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
    get_current_user
)

router = APIRouter(prefix='/user', tags=['User'])


@router.post("/register", response_model=UserResponse)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    user = db.query(Users).filter(Users.username == user_in.username).first()
    if user:
        raise HTTPException(status_code=400, detail="Username already registered")

    new_employee = Employers(
        telegram_name=user_in.employee.telegram_name,
        full_name=user_in.employee.full_name,
        join_date=user_in.employee.join_date
    )
    db.add(new_employee)
    db.commit()
    db.refresh(new_employee)

    hashed_password = get_password_hash(user_in.password)
    new_user = Users(
        username=user_in.username,
        hashed_password=hashed_password,
        employee_id=new_employee.pk_employee
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {
        "username": new_user.username,
        "employee": new_employee
    }


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

    token_data = {"sub": user.username}
    access_token = create_access_token(data=token_data)
    return Token(access_token=access_token)


@router.post("/logout")
def logout(user_data: Dict = Depends(get_current_user)):
    token_blacklist.add(user_data['token'])
    return {"msg": "Successfully logged out"}


@router.get("/me", response_model=UserResponse)
def get_me(user_data: Dict = Depends(get_current_user)):
    return {
        "username": user_data["user"].username,
        "employee": user_data["employee"]
    }
