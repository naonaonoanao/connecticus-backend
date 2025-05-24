import traceback
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from uuid import UUID

from app.models.models import Employers
from app.schemas.schemas import EmployeeCreate, EmployeeRead, EmployeeUpdate, MessageDTO, EmployeeListWithMeta
from app.db.get_db import get_db
from app.services.user_service import check_unique_fields, get_current_user, update_entity, get_employee_with_id, \
    get_employees_lst, get_employees_lst_common

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


@router.get("/employees/filters", response_model=EmployeeListWithMeta)
async def get_employees_list_filters(
        first_name: Optional[List[str]] = Query(None),
        last_name: Optional[List[str]] = Query(None),
        middle_name: Optional[List[str]] = Query(None),
        email: Optional[List[str]] = Query(None),
        phone_number: Optional[List[str]] = Query(None),
        telegram_name: Optional[List[str]] = Query(None),
        city: Optional[List[str]] = Query(None),
        id_position: Optional[List[str]] = Query(None),
        id_department: Optional[List[str]] = Query(None),
        id_interest: Optional[List[str]] = Query(None, description="Filter by interest IDs"),
        id_technology: Optional[List[str]] = Query(None, description="Filter by technology IDs"),
        id_project: Optional[List[str]] = Query(None, description="Filter by project IDs"),
        skip: int = Query(0, ge=0),
        limit: int = Query(10, ge=1),
        db: Session = Depends(get_db)
):
    filters = {
        "first_name": first_name,
        "last_name": last_name,
        "middle_name": middle_name,
        "email": email,
        "phone_number": phone_number,
        "telegram_name": telegram_name,
        "city": city,
        "id_position": id_position,
        "id_department": id_department,
        "id_interest": id_interest,
        "id_technology": id_technology,
        "id_project": id_project,
    }

    result = get_employees_lst(db, filters=filters, skip=skip, limit=limit)
    ans = {
        "meta": {
            "total_count": result['total_count'],
            "total_pages": result['total_pages'],
            "skip": skip,
            "limit": limit
        },
        "data": result['employees']
    }

    return ans


@router.get("/employees/search", response_model=EmployeeListWithMeta)
async def get_employees_list_search(
        str_to_find: str = "",
        skip: int = Query(0, ge=0),
        limit: int = Query(10, ge=1),
        db: Session = Depends(get_db)
):
    result = get_employees_lst_common(db, str_to_find=str_to_find, skip=skip, limit=limit)
    ans = {
        "meta": {
            "total_count": result['total_count'],
            "total_pages": result['total_pages'],
            "skip": skip,
            "limit": limit
        },
        "data": result['employees']
    }

    return ans


@router.get("/{employee_id}", response_model=EmployeeRead)
async def get_employee(
        employee_id: UUID,
        db: Session = Depends(get_db)
):
    employee = get_employee_with_id(db, str(employee_id))

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

        updated_employee = await update_entity(
            db=db,
            entity=user_data['employee'],
            entity_updated_data=employee_update.dict()
        )

        return MessageDTO(message=f"Employee {updated_employee.id_employee} successfully")
    except HTTPException:
        raise
    except Exception:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Internal error")
