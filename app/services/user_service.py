import math
from datetime import datetime, timedelta
from typing import Dict, Any, List
from uuid import UUID

import jwt
from fastapi import Depends, HTTPException, status, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from passlib.context import CryptContext

from typing import Optional

from sqlalchemy import or_, distinct, func
from sqlalchemy.orm import Session

from app.models.models import (
    Interests,
    Technologies, Ranks,
    Projects, Roles,
    Positions, Departments, Employers, Notifications, NotificationsEmployees
)
from app.core.config import settings
from app.db.get_db import get_db
from app.models.models import Users, InterestsEmployers, TechnologyEmployee, ProjectsEmployers

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

failed_attempts_cache = {}
token_blacklist = set()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


async def get_current_user(credentials: HTTPAuthorizationCredentials = Security(security),
                           db: Session = Depends(get_db)):
    token = credentials.credentials

    if token in token_blacklist:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has been revoked")
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
    except jwt.PyJWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials")

    user = db.query(Users).filter(Users.username == username).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return {"user": user, "employee": user.employee, "token": token, "role": user.role_id}


def get_user_with_related(db: Session, username: str) -> Optional[Dict[str, Any]]:
    user = db.query(Users).filter(Users.username == username).first()
    if not user or not user.employee:
        return None

    emp = user.employee

    # Basic employee fields
    emp_data: Dict[str, Any] = {
        "id_employee": emp.id_employee,
        "first_name": emp.first_name,
        "last_name": emp.last_name,
        "middle_name": emp.middle_name,
        "date_of_birth": emp.date_of_birth,
        "email": emp.email,
        "phone_number": emp.phone_number,
        "telegram_name": emp.telegram_name,
        "city": emp.city,
    }

    # position and department
    position = db.query(Positions).get(emp.id_position)
    department = db.query(Departments).get(emp.id_department)
    emp_data["position"] = {
        "id_position": position.id_position,
        "position_name": position.position_name
    } if position else None
    emp_data["department"] = {
        "id_department": department.id_department,
        "name_department": department.name_department
    } if department else None

    # interests
    interests = (
        db.query(Interests)
            .join(InterestsEmployers, Interests.id_interest == InterestsEmployers.id_interest)
            .filter(InterestsEmployers.id_employee == emp.id_employee)
            .all()
    )
    emp_data["interests"] = [
        {"id_interest": i.id_interest, "name_interest": i.name_interest} for i in interests
    ]

    # technologies with rank
    tech_rows = (
        db.query(Technologies, Ranks)
            .join(TechnologyEmployee, Technologies.id_technology == TechnologyEmployee.id_technology)
            .join(Ranks, TechnologyEmployee.id_rank == Ranks.id_rank)
            .filter(TechnologyEmployee.id_employee == emp.id_employee)
            .all()
    )
    emp_data["technologies"] = [
        {
            "id_technology": tech.id_technology,
            "name_technology": tech.name_technology,
            "rank": {"id_rank": rank.id_rank, "name_rank": rank.name_rank}
        }
        for tech, rank in tech_rows
    ]

    # projects
    proj_rows = (
        db.query(Projects, Roles)
            .join(ProjectsEmployers, Projects.id_project == ProjectsEmployers.id_project)
            .join(Roles, ProjectsEmployers.id_role == Roles.id_role)
            .filter(ProjectsEmployers.id_employee == emp.id_employee)
            .all()
    )
    emp_data["projects"] = [
        {
            "id_project": proj.id_project,
            "name_project": proj.name_project,
            "role": {
                "id_role": role.id_role,
                "name_role": role.name_role
            }
        } for proj, role in proj_rows
    ]

    return {"username": user.username, "employee": emp_data}


def get_employee_with_id(db: Session, id_employee: str) -> Optional[Dict[str, Any]]:
    emp = db.query(Employers).filter(Employers.id_employee == id_employee).first()
    if not emp:
        return None

    # Basic employee fields
    emp_data: Dict[str, Any] = {
        "id_employee": emp.id_employee,
        "first_name": emp.first_name,
        "last_name": emp.last_name,
        "middle_name": emp.middle_name,
        "date_of_birth": emp.date_of_birth,
        "email": emp.email,
        "phone_number": emp.phone_number,
        "telegram_name": emp.telegram_name,
        "city": emp.city,
    }

    # position and department
    position = db.query(Positions).get(emp.id_position)
    department = db.query(Departments).get(emp.id_department)
    emp_data["position"] = {
        "id_position": position.id_position,
        "position_name": position.position_name
    } if position else None
    emp_data["department"] = {
        "id_department": department.id_department,
        "name_department": department.name_department
    } if department else None

    # interests
    interests = (
        db.query(Interests)
            .join(InterestsEmployers, Interests.id_interest == InterestsEmployers.id_interest)
            .filter(InterestsEmployers.id_employee == emp.id_employee)
            .all()
    )
    emp_data["interests"] = [
        {"id_interest": i.id_interest, "name_interest": i.name_interest} for i in interests
    ]

    # technologies with rank
    tech_rows = (
        db.query(Technologies, Ranks)
            .join(TechnologyEmployee, Technologies.id_technology == TechnologyEmployee.id_technology)
            .join(Ranks, TechnologyEmployee.id_rank == Ranks.id_rank)
            .filter(TechnologyEmployee.id_employee == emp.id_employee)
            .all()
    )
    emp_data["technologies"] = [
        {
            "id_technology": tech.id_technology,
            "name_technology": tech.name_technology,
            "rank": {"id_rank": rank.id_rank, "name_rank": rank.name_rank}
        }
        for tech, rank in tech_rows
    ]

    # projects
    proj_rows = (
        db.query(Projects, Roles)
            .join(ProjectsEmployers, Projects.id_project == ProjectsEmployers.id_project)
            .join(Roles, ProjectsEmployers.id_role == Roles.id_role)
            .filter(ProjectsEmployers.id_employee == emp.id_employee)
            .all()
    )
    emp_data["projects"] = [
        {
            "id_project": proj.id_project,
            "name_project": proj.name_project,
            "role": {
                "id_role": role.id_role,
                "name_role": role.name_role
            }
        } for proj, role in proj_rows
    ]

    return emp_data


def get_employees_list(
        db: Session,
        *,
        str_to_find: Optional[str] = None,
        filters: Dict[str, Optional[List[str]]],
        skip: int = 0,
        limit: int = 10
) -> Dict[str, Any]:
    query = db.query(Employers)

    if str_to_find:
        pattern = f"%{str_to_find}%"
        query = (
            query
                .outerjoin(InterestsEmployers, InterestsEmployers.id_employee == Employers.id_employee)
                .outerjoin(Interests, Interests.id_interest == InterestsEmployers.id_interest)
                .outerjoin(TechnologyEmployee, TechnologyEmployee.id_employee == Employers.id_employee)
                .outerjoin(Technologies, Technologies.id_technology == TechnologyEmployee.id_technology)
                .outerjoin(Ranks, Ranks.id_rank == TechnologyEmployee.id_rank)
                .outerjoin(ProjectsEmployers, ProjectsEmployers.id_employee == Employers.id_employee)
                .outerjoin(Projects, Projects.id_project == ProjectsEmployers.id_project)
                .outerjoin(Roles, Roles.id_role == ProjectsEmployers.id_role)
        )

        or_clauses = [
            Employers.first_name.ilike(pattern),
            Employers.last_name.ilike(pattern),
            Employers.middle_name.ilike(pattern),
            Employers.email.ilike(pattern),
            Employers.phone_number.ilike(pattern),
            Employers.telegram_name.ilike(pattern),
            Employers.city.ilike(pattern),
            Interests.name_interest.ilike(pattern),
            Technologies.name_technology.ilike(pattern),
            Ranks.name_rank.ilike(pattern),
            Projects.name_project.ilike(pattern),
            Roles.name_role.ilike(pattern),
        ]
        query = query.filter(or_(*or_clauses))

    text_fields = [
        ("first_name", Employers.first_name),
        ("last_name", Employers.last_name),
        ("middle_name", Employers.middle_name),
        ("email", Employers.email),
        ("phone_number", Employers.phone_number),
        ("telegram_name", Employers.telegram_name),
        ("city", Employers.city),
    ]
    for key, column in text_fields:
        vals = filters.get(key)
        if vals:
            query = query.filter(or_(*[column.ilike(f"%{v}%") for v in vals]))

    if filters.get("id_position"):
        query = query.filter(Employers.id_position.in_(filters["id_position"]))
    if filters.get("id_department"):
        query = query.filter(Employers.id_department.in_(filters["id_department"]))

    if filters.get("id_interest"):
        query = (
            query
                .join(InterestsEmployers, InterestsEmployers.id_employee == Employers.id_employee)
                .filter(InterestsEmployers.id_interest.in_(filters["id_interest"]))
        )
    if filters.get("id_technology"):
        query = (
            query
                .join(TechnologyEmployee, TechnologyEmployee.id_employee == Employers.id_employee)
                .filter(TechnologyEmployee.id_technology.in_(filters["id_technology"]))
        )
    if filters.get("id_project"):
        query = (
            query
                .join(ProjectsEmployers, ProjectsEmployers.id_employee == Employers.id_employee)
                .filter(ProjectsEmployers.id_project.in_(filters["id_project"]))
        )

    base_q = query.distinct(Employers.id_employee)
    total_count = (
        db.query(func.count(distinct(Employers.id_employee)))
            .select_from(base_q.subquery())
            .scalar()
    )
    total_pages = math.ceil(total_count / limit) if limit > 0 else 1

    employees = base_q.offset(skip).limit(limit).all()

    result: List[Dict[str, Any]] = []
    for emp in employees:
        emp_data: Dict[str, Any] = {
            "id_employee": emp.id_employee,
            "first_name": emp.first_name,
            "last_name": emp.last_name,
            "middle_name": emp.middle_name,
            "date_of_birth": emp.date_of_birth,
            "email": emp.email,
            "phone_number": emp.phone_number,
            "telegram_name": emp.telegram_name,
            "city": emp.city,
        }

        pos = db.query(Positions).get(emp.id_position)
        dept = db.query(Departments).get(emp.id_department)
        emp_data["position"] = {"id_position": pos.id_position, "position_name": pos.position_name} if pos else None
        emp_data["department"] = {"id_department": dept.id_department,
                                  "name_department": dept.name_department} if dept else None

        ints = (
            db.query(Interests)
                .join(InterestsEmployers, Interests.id_interest == InterestsEmployers.id_interest)
                .filter(InterestsEmployers.id_employee == emp.id_employee)
                .all()
        )
        emp_data["interests"] = [{"id_interest": i.id_interest, "name_interest": i.name_interest} for i in ints]

        techs = (
            db.query(Technologies, Ranks)
                .join(TechnologyEmployee, Technologies.id_technology == TechnologyEmployee.id_technology)
                .join(Ranks, TechnologyEmployee.id_rank == Ranks.id_rank)
                .filter(TechnologyEmployee.id_employee == emp.id_employee)
                .all()
        )
        emp_data["technologies"] = [
            {
                "id_technology": t.id_technology,
                "name_technology": t.name_technology,
                "rank": {
                    "id_rank": r.id_rank,
                    "name_rank": r.name_rank
                }
            } for t, r in techs
        ]

        projs = (
            db.query(Projects, Roles)
                .join(ProjectsEmployers, Projects.id_project == ProjectsEmployers.id_project)
                .join(Roles, ProjectsEmployers.id_role == Roles.id_role)
                .filter(ProjectsEmployers.id_employee == emp.id_employee)
                .all()
        )
        emp_data["projects"] = [
            {
                "id_project": p.id_project,
                "name_project": p.name_project,
                "role": {
                    "id_role": rl.id_role,
                    "name_role": rl.name_role
                }
            } for p, rl in projs
        ]

        result.append(emp_data)

    return {
        "employees": result,
        "total_count": total_count,
        "total_pages": total_pages,
    }


async def check_unique_fields(
        db: Session,
        employee_id: UUID,
        email: str = None,
        phone: str = None,
        telegram: str = None
):
    duplicated_fields = []

    if email:
        existing = db.query(Employers).filter(
            Employers.email == email, Employers.id_employee != employee_id
        ).first()
        if existing:
            duplicated_fields.append("email")

    if phone:
        existing = db.query(Employers).filter(
            Employers.phone_number == phone, Employers.id_employee != employee_id
        ).first()
        if existing:
            duplicated_fields.append("phone_number")

    if telegram:
        existing = db.query(Employers).filter(
            Employers.telegram_name == telegram, Employers.id_employee != employee_id
        ).first()
        if existing:
            duplicated_fields.append("telegram_name")

    return duplicated_fields


async def update_entity(db: Session, entity, entity_updated_data: Dict):
    for field, value in entity_updated_data.items():
        setattr(entity, field, value)

    db.commit()
    db.refresh(entity)

    return entity


def create_notification(db: Session, content: str, employee_ids: List[UUID]) -> UUID:
    new_notif = Notifications(content=content)
    db.add(new_notif)
    db.flush()

    for emp_id in employee_ids:
        assoc = NotificationsEmployees(
            id_notification=new_notif.id,
            id_employee=emp_id,
            is_shown=False
        )
        db.add(assoc)

    db.commit()
    db.refresh(new_notif)

    return new_notif.id
