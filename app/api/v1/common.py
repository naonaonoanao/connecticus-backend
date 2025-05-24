from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import distinct

from app.db.get_db import get_db
from app.models.models import (
    Employers,
    Positions,
    Departments,
    Projects,
    Technologies,
    Interests,
)
from app.schemas.schemas import PositionRead, DepartmentRead, TechnologyRead, InterestsRead, ProjectRead, \
    TechnologySoloRead

router = APIRouter(prefix='/common', tags=['Common'])


@router.get("/cities", response_model=List[str])
async def list_cities(db: Session = Depends(get_db)):
    rows = db.query(distinct(Employers.city)).order_by(Employers.city).all()
    return [city for (city,) in rows]


@router.get("/positions", response_model=List[PositionRead])
async def list_positions(db: Session = Depends(get_db)):
    positions = db.query(Positions).order_by(Positions.position_name).all()
    return positions


@router.get("/departments", response_model=List[DepartmentRead])
async def list_departments(db: Session = Depends(get_db)):
    depts = db.query(Departments).order_by(Departments.name_department).all()
    return depts


@router.get("/projects", response_model=List[ProjectRead])
async def list_projects(db: Session = Depends(get_db)):
    projs = db.query(Projects).order_by(Projects.name_project).all()
    return projs


@router.get("/technologies", response_model=List[TechnologySoloRead])
async def list_technologies(db: Session = Depends(get_db)):
    techs = db.query(Technologies).order_by(Technologies.name_technology).all()
    return techs


@router.get("/interests", response_model=List[InterestsRead])
async def list_interests(db: Session = Depends(get_db)):
    ints = db.query(Interests).order_by(Interests.name_interest).all()
    return ints
