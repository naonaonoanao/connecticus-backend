from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID

from app.models.models import Employees
from app.schemas.schemas import EmployeeCreate, EmployeeRead
from app.db.get_db import get_db


router = APIRouter(prefix='/employee', tags=['Employee'])


@router.post("", response_model=EmployeeRead)
def create_employee(
    employee_in: EmployeeCreate,
    db: Session = Depends(get_db)
):
    db_employee = Employees(
        telegram_name=employee_in.telegram_name,
        join_date=employee_in.join_date,
        full_name=employee_in.full_name
    )
    db.add(db_employee)
    db.commit()
    db.refresh(db_employee)
    return db_employee


@router.get("/{employee_id}", response_model=EmployeeRead)
def get_employee(
    employee_id: UUID,
    db: Session = Depends(get_db)
):
    employee = db.query(Employees).filter(Employees.pk_employee == employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    return employee
