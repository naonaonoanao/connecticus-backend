import re

from pydantic import BaseModel, constr, EmailStr, field_validator, model_validator, ConfigDict
from typing import Optional, List, Union
from uuid import UUID
from datetime import date


class MessageDTO(BaseModel):
    message: str


class ProjectRead(BaseModel):
    id_project: UUID
    name_project: str
    description: str


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


class TechnologySoloRead(BaseModel):
    id_technology: UUID
    name_technology: str


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


class InterestInput(BaseModel):
    id: Optional[UUID] = None
    name: Optional[str] = None

    @model_validator(mode="before")
    def check_either_id_or_name(cls, values):
        if not values.get("id") and not values.get("name"):
            raise ValueError("Нужно указать либо id, либо name интереса")
        return values


class ExistingInterestInput(BaseModel):
    id: UUID


class NewInterestInput(BaseModel):
    name_interest: constr(strip_whitespace=True, min_length=1, max_length=52)


class EmployeeInterestsUpdate(BaseModel):
    interests: list[Union[ExistingInterestInput, NewInterestInput]]


class TechnologyRankInput(BaseModel):
    id_technology: UUID
    id_rank: UUID


class ExistingTechnologyInput(BaseModel):
    id_technology: UUID
    id_rank: UUID


class NewTechnologyInput(BaseModel):
    name_technology: constr(strip_whitespace=True, min_length=1, max_length=52)
    description: constr(strip_whitespace=True, min_length=1, max_length=52)
    id_rank: UUID


class EmployeeTechnologiesUpdate(BaseModel):
    technologies: List[Union[ExistingTechnologyInput, NewTechnologyInput]]


class ProjectRoleInput(BaseModel):
    id_project: UUID
    id_role: UUID


class EmployeeProjectsUpdate(BaseModel):
    projects: List[ProjectRoleInput]


class EventCreate(BaseModel):
    name_event: constr(strip_whitespace=True, min_length=1, max_length=52)
    date: date
    place: constr(strip_whitespace=True, min_length=1, max_length=52)
    id_event_type: UUID
    attendee_ids: Optional[List[UUID]] = []

    model_config = ConfigDict(from_attributes=True)


class EventUpdate(BaseModel):
    name_event: constr(strip_whitespace=True, min_length=1, max_length=52)
    date: date
    place: constr(strip_whitespace=True, min_length=1, max_length=52)
    id_event_type: UUID


class EmployeeSummary(BaseModel):
    id_employee: UUID
    first_name: str
    last_name: str

    model_config = ConfigDict(
        from_attributes=True
    )


class EventTypeRead(BaseModel):
    id_event_type: UUID
    name_type: str

    model_config = ConfigDict(from_attributes=True)


class EventRead(BaseModel):
    id_event: UUID
    name_event: str
    date: date
    place: str
    owner: EmployeeSummary
    event_type: EventTypeRead
    attendees: List[EmployeeSummary] = []

    class Config:
        orm_mode = True

    @classmethod
    def from_orm(cls, event, event_type_summary, owner_summary, attendees: List[EmployeeSummary]):
        return cls(
            id_event=event.id_event,
            name_event=event.name_event,
            date=event.date,
            place=event.place,
            owner=owner_summary,
            event_type=event_type_summary,
            attendees=attendees,
        )


class PaginatedEvents(BaseModel):
    total_count: int
    total_pages: int
    skip: int
    limit: int
    events: List[EventRead]
