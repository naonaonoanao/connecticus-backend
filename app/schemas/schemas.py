from pydantic import BaseModel
from typing import Optional, List
from uuid import UUID
from datetime import date


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
