import traceback
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from uuid import UUID

from app.models.models import Employers, InterestsEmployers, TechnologyEmployee, ProjectsEmployers, Interests, \
    Technologies
from app.schemas.schemas import EmployeeCreate, EmployeeRead, EmployeeUpdate, MessageDTO, EmployeeListWithMeta, \
    EmployeeInterestsUpdate, EmployeeTechnologiesUpdate, EmployeeProjectsUpdate, NewTechnologyInput, \
    ExistingTechnologyInput, NewInterestInput, ExistingInterestInput, HrEmployeeUpdate, EmployeeCreateHr
from app.db.get_db import get_db
from app.services.user_service import check_unique_fields, get_current_user, update_entity, get_employee_with_id, \
    get_employees_list

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


@router.get(
    "/employees",
    response_model=EmployeeListWithMeta
)
async def list_employees(
        str_to_find: Optional[str] = Query(None, description="Общий поиск по всем полям"),
        first_name: Optional[List[str]] = Query(None),
        last_name: Optional[List[str]] = Query(None),
        middle_name: Optional[List[str]] = Query(None),
        email: Optional[List[str]] = Query(None),
        phone_number: Optional[List[str]] = Query(None),
        telegram_name: Optional[List[str]] = Query(None),
        city: Optional[List[str]] = Query(None),
        id_position: Optional[List[str]] = Query(None),
        id_department: Optional[List[str]] = Query(None),
        id_interest: Optional[List[str]] = Query(None),
        id_technology: Optional[List[str]] = Query(None),
        id_project: Optional[List[str]] = Query(None),
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
    res = get_employees_list(
        db,
        str_to_find=str_to_find,
        filters=filters,
        skip=skip,
        limit=limit
    )
    return {
        "data": res["employees"],
        "meta": {
            "total_count": res["total_count"],
            "total_pages": res["total_pages"],
            "skip": skip,
            "limit": limit
        }
    }


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


@router.put("/hr/{employee_id}", response_model=MessageDTO)
async def edit_employee_hr(
        employee_update: HrEmployeeUpdate,
        emp_id: UUID,
        user_data: Dict = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    try:
        duplicated_fields = await check_unique_fields(
            db=db,
            employee_id=emp_id,
            email=employee_update.email,
            phone=employee_update.phone_number,
            telegram=employee_update.telegram_name
        )

        if duplicated_fields:
            raise HTTPException(status_code=400, detail=f"{str(duplicated_fields)} already in use")

        updated_employee = await update_entity(
            db=db,
            entity=db.query(Employers).filter(Employers.id_employee == emp_id).first(),
            entity_updated_data=employee_update.dict()
        )

        return MessageDTO(message=f"Employee {updated_employee.id_employee} successfully")
    except HTTPException:
        raise
    except Exception:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Internal error")


@router.delete("/hr/{employee_id}", response_model=MessageDTO)
async def delete_employee_hr(
    employee_id: UUID,
    user_data: Dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        employee = db.query(Employers).filter_by(id_employee=str(employee_id)).first()
        if not employee:
            raise HTTPException(status_code=404, detail="Employee not found")

        db.query(InterestsEmployers).filter_by(id_employee=str(employee_id)).delete()
        db.query(TechnologyEmployee).filter_by(id_employee=str(employee_id)).delete()
        db.query(ProjectsEmployers).filter_by(id_employee=str(employee_id)).delete()

        db.delete(employee)
        db.commit()

        return MessageDTO(message=f"Employee {employee_id} deleted successfully")
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Error deleting employee")


@router.post("/hr")
async def create_employee_hr(
    employee_in: EmployeeCreateHr,
    user_data: Dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        # Проверяем уникальность полей
        duplicated_fields = await check_unique_fields(
            db=db,
            email=employee_in.email,
            phone=employee_in.phone_number,
            telegram=employee_in.telegram_name
        )
        if duplicated_fields:
            raise HTTPException(status_code=400, detail=f"{str(duplicated_fields)} already in use")

        db_employee = Employers(
            first_name=employee_in.first_name,
            last_name=employee_in.last_name,
            middle_name=employee_in.middle_name,
            date_of_birth=employee_in.date_of_birth,
            id_position=employee_in.id_position,
            id_department=employee_in.id_department,
            telegram_name=employee_in.telegram_name,
            email=employee_in.email,
            phone_number=employee_in.phone_number,
            city=employee_in.city
        )
        db.add(db_employee)
        db.commit()
        db.refresh(db_employee)

        return db_employee
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Internal server error")


# для hr
@router.put("/{employee_id}/interests", response_model=MessageDTO)
async def update_employee_interests(
    employee_id: UUID,
    update_data: EmployeeInterestsUpdate,
    db: Session = Depends(get_db),
    user_data: Dict = Depends(get_current_user)
):
    try:
        # Удаляем текущие интересы
        db.query(InterestsEmployers).filter_by(id_employee=employee_id).delete()

        for interest in update_data.interests:
            if isinstance(interest, ExistingInterestInput):
                # Проверяем, что интерес существует
                existing = db.query(Interests).filter_by(id_interest=interest.id).first()
                if not existing:
                    raise HTTPException(status_code=400, detail=f"Интереса с ID {interest.id} не существует")
                interest_id = existing.id_interest

            elif isinstance(interest, NewInterestInput):
                # Проверяем, есть ли уже интерес с таким именем
                existing = db.query(Interests).filter_by(name_interest=interest.name_interest).first()
                if existing:
                    interest_id = existing.id_interest
                else:
                    new_interest = Interests(name_interest=interest.name_interest)
                    db.add(new_interest)
                    db.flush()  # Получаем ID нового интереса
                    interest_id = new_interest.id_interest

            # Добавляем связь
            db.add(InterestsEmployers(id_employee=employee_id, id_interest=interest_id))

        db.commit()
        return MessageDTO(message=f"Интересы сотрудника {employee_id} обновлены")

    except HTTPException:
        raise
    except Exception:
        db.rollback()
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Ошибка при обновлении интересов")


@router.put("/me/interests", response_model=MessageDTO)
async def update_employee_interests(
    update_data: EmployeeInterestsUpdate,
    db: Session = Depends(get_db),
    user_data: Dict = Depends(get_current_user)
):
    try:
        employee_id = user_data['employee'].id_employee

        # Удаляем старые связи
        db.query(InterestsEmployers).filter_by(id_employee=employee_id).delete()

        for interest in update_data.interests:
            if isinstance(interest, ExistingInterestInput):
                # Проверим, что интерес с таким id существует
                exists = db.query(Interests).filter_by(id_interest=interest.id).first()
                if not exists:
                    raise HTTPException(status_code=400, detail=f"Интереса с ID {interest.id} не существует")
                db.add(InterestsEmployers(id_employee=employee_id, id_interest=interest.id))

            elif isinstance(interest, NewInterestInput):
                # Ищем по имени — если есть, берем; если нет — создаем
                existing = db.query(Interests).filter_by(name_interest=interest.name_interest).first()
                if not existing:
                    new_interest = Interests(name_interest=interest.name_interest)
                    db.add(new_interest)
                    db.flush()  # получим id
                    interest_id = new_interest.id_interest
                else:
                    interest_id = existing.id_interest

                db.add(InterestsEmployers(id_employee=employee_id, id_interest=interest_id))

        db.commit()
        return MessageDTO(message=f"Интересы сотрудника {employee_id} обновлены")

    except HTTPException:
        raise
    except Exception:
        db.rollback()
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Ошибка при обновлении интересов")


@router.put("/me/technologies", response_model=MessageDTO)
async def update_my_technologies(
    update_data: EmployeeTechnologiesUpdate,
    db: Session = Depends(get_db),
    user_data: Dict = Depends(get_current_user)
):
    employee_id = user_data['employee'].id_employee
    try:
        existing_ids = set()
        new_names = set()
        name_to_rank = {}

        for tech in update_data.technologies:
            if isinstance(tech, ExistingTechnologyInput):
                if tech.id_technology in existing_ids:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Технология с ID {tech.id_technology} указана несколько раз"
                    )
                existing_ids.add(tech.id_technology)

            elif isinstance(tech, NewTechnologyInput):
                clean_name = tech.name_technology.strip().lower()
                if clean_name in new_names:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Новая технология '{tech.name_technology}' указана несколько раз"
                    )
                if clean_name in [name.strip().lower() for name in name_to_rank]:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Конфликт: технология '{tech.name_technology}' указана и как существующая, и как новая"
                    )
                new_names.add(clean_name)

        # Удаляем старые связи
        db.query(TechnologyEmployee).filter_by(id_employee=employee_id).delete()

        for tech in update_data.technologies:
            if isinstance(tech, ExistingTechnologyInput):
                # Проверим, что технология с таким ID существует
                exists = db.query(Technologies).filter_by(id_technology=tech.id_technology).first()
                if not exists:
                    raise HTTPException(status_code=400, detail=f"Технологии с ID {tech.id_technology} не существует")

                db.add(TechnologyEmployee(
                    id_employee=employee_id,
                    id_technology=tech.id_technology,
                    id_rank=tech.id_rank
                ))

            elif isinstance(tech, NewTechnologyInput):
                name_clean = tech.name_technology.strip()
                desc_clean = tech.description.strip()

                # Проверим, существует ли технология с таким именем
                existing = db.query(Technologies).filter_by(name_technology=name_clean).first()
                if existing:
                    tech_id = existing.id_technology
                else:
                    new_tech = Technologies(
                        name_technology=name_clean,
                        description=desc_clean
                    )
                    db.add(new_tech)
                    db.flush()  # получим id_technology
                    tech_id = new_tech.id_technology

                db.add(TechnologyEmployee(
                    id_employee=employee_id,
                    id_technology=tech_id,
                    id_rank=tech.id_rank
                ))

        db.commit()
        return MessageDTO(message=f"Технологии сотрудника {employee_id} обновлены")

    except HTTPException:
        raise
    except Exception:
        db.rollback()
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Ошибка при обновлении технологий")


# для hr
@router.put("/{employee_id}/technologies", response_model=MessageDTO)
async def update_employee_technologies(
    employee_id: UUID,
    update_data: EmployeeTechnologiesUpdate,
    db: Session = Depends(get_db),
    user_data: Dict = Depends(get_current_user)
):
    try:
        db.query(TechnologyEmployee).filter_by(id_employee=employee_id).delete()

        for tech in update_data.technologies:
            db.add(TechnologyEmployee(
                id_employee=employee_id,
                id_technology=tech.id_technology,
                id_rank=tech.id_rank
            ))

        db.commit()
        return MessageDTO(message=f"Технологии сотрудника {employee_id} обновлены")
    except Exception:
        db.rollback()
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Ошибка при обновлении технологий")
