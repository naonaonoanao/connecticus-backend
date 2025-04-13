from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import date


class EmployeeCreate(BaseModel):
    telegram_name: str
    join_date: Optional[date]
    full_name: str


class EmployeeRead(BaseModel):
    pk_employee: UUID
    telegram_name: str
    join_date: Optional[date]
    full_name: str

    class Config:
        orm_mode = True


class UserCreate(BaseModel):
    username: str
    password: str
    employee: EmployeeCreate


class UserResponse(BaseModel):
    username: str
    employee: EmployeeRead

    class Config:
        orm_mode = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class LoginDTO(BaseModel):
    username: str
    password: str
