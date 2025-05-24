import re

from pydantic import BaseModel, constr, EmailStr, field_validator
from typing import Optional, List
from uuid import UUID
from datetime import date


class MessageDTO(BaseModel):
    message: str


class InterestsRead(BaseModel):
    id_interest: UUID
    name_interest: str


class RankRead(BaseModel):
    id_rank: UUID
    name_rank: str


class TechnologyRead(BaseModel):
    id_technology: UUID
    name_technology: str
    rank: RankRead


class DepartmentRead(BaseModel):
    id_department: UUID
    name_department: str


class RoleRead(BaseModel):
    id_role: UUID
    name_role: str


class PositionRead(BaseModel):
    id_position: UUID
    position_name: str


class ProjectsUserRead(BaseModel):
    id_project: UUID
    name_project: str
    role: RoleRead


class EmployeeCreate(BaseModel):
    telegram_name: str
    join_date: Optional[date]
    full_name: str


class EmployeeRead(BaseModel):
    id_employee: UUID
    first_name: str
    last_name: str
    middle_name: Optional[str]
    date_of_birth: date
    email: str
    phone_number: str
    telegram_name: str
    city: str
    position: Optional[PositionRead]
    department: Optional[DepartmentRead]
    technologies: List[TechnologyRead]
    interests: List[InterestsRead]
    projects: List[ProjectsUserRead]

    class Config:
        orm_mode = True


class PaginationMeta(BaseModel):
    total_count: int
    total_pages: int
    skip: int
    limit: int


class EmployeeListWithMeta(BaseModel):
    data: List[EmployeeRead]
    meta: PaginationMeta


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


class GraphNode(BaseModel):
    id: str
    name: str
    group: str


class GraphLink(BaseModel):
    source: str
    target: str


class GraphViewDTO(BaseModel):
    nodes: List[GraphNode]
    links: List[GraphLink]


class EmployeeUpdate(BaseModel):
    first_name: constr(strip_whitespace=True, min_length=1, max_length=50)
    last_name: Optional[constr(strip_whitespace=True, min_length=1, max_length=50)]
    middle_name: constr(strip_whitespace=True, min_length=1, max_length=50)
    date_of_birth: date
    email: EmailStr
    phone_number: constr(strip_whitespace=True, min_length=10, max_length=20)
    telegram_name: constr(strip_whitespace=True, min_length=3, max_length=32)
    city: constr(strip_whitespace=True, min_length=1, max_length=100)

    @field_validator('phone_number')
    def validate_phone(cls, v):
        if v and not re.match(r'^[\d\s\-\+\(\)]+$', v):
            raise ValueError('Недопустимый формат номера телефона')
        return v

    @field_validator('telegram_name')
    def validate_telegram_name(cls, v):
        if v and not re.match(r'^[a-zA-Z0-9_]{3,32}$', v):
            raise ValueError('Недопустимый Telegram username: допустимы только буквы, цифры и _')
        return v

    @field_validator('date_of_birth')
    def validate_dob(cls, v):
        if v and v > date.today():
            raise ValueError('Дата рождения не может быть в будущем')
        return v
