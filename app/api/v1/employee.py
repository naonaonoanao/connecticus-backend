import traceback
from typing import Dict

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID

from app.models.models import Employers
from app.schemas.schemas import EmployeeCreate, EmployeeRead, EmployeeUpdate, MessageDTO
from app.db.get_db import get_db
from app.services.user_service import check_unique_fields, get_current_user, update_employee

router = APIRouter(prefix='/employee', tags=['Employee'])


@router.post("", response_model=EmployeeRead)
async def create_employee(
    employee_in: EmployeeCreate,
    db: Session = Depends(get_db)
):
    db_employee = Employers(
        telegram_name=employee_in.telegram_name,
        join_date=employee_in.join_date,
        full_name=employee_in.full_name
    )
    db.add(db_employee)
    db.commit()
    db.refresh(db_employee)
    return db_employee


@router.get("/{employee_id}", response_model=EmployeeRead)
async def get_employee(
    employee_id: UUID,
    db: Session = Depends(get_db)
):
    employee = db.query(Employers).filter(Employers.pk_employee == employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    return employee


@router.put("/{employee_id}", response_model=MessageDTO)
async def edit_employee(
    employee_update: EmployeeUpdate,
    user_data: Dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        duplicated_fields = await check_unique_fields(
            db=db,
            employee_id=user_data['employee'].id_employee,
            email=employee_update.email,
            phone=employee_update.phone_number,
            telegram=employee_update.telegram_name
        )

        if duplicated_fields:
            raise HTTPException(status_code=400, detail=f"{str(duplicated_fields)} already in use")

        updated_employee = await update_employee(
            db=db,
            employee=user_data['employee'],
            employee_updated_data=employee_update.dict()
        )

        return MessageDTO(message=f"Employee {updated_employee.id_employee} successfully")
    except HTTPException:
        raise
    except Exception:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Internal error")
