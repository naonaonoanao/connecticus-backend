from datetime import datetime, timedelta
from typing import Dict, Any
import jwt
from fastapi import Depends, HTTPException, status, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from passlib.context import CryptContext

from typing import Optional
from sqlalchemy.orm import Session

from app.models.models import (
    Interests,
    Technologies, Ranks,
    Projects, Roles,
    Positions, Departments
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
    return {"user": user, "employee": user.employee, "token": token}


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
    emp_data["position"] = {"id_position": position.id_position, "position_name": position.position_name} if position else None
    emp_data["department"] = {"id_department": department.id_department, "name_department": department.name_department} if department else None

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
        {"id_project": proj.id_project, "name_project": proj.name_project, "role": {"id_role": role.id_role, "name_role": role.name_role}} for proj, role in proj_rows
    ]

    return {"username": user.username, "employee": emp_data}
