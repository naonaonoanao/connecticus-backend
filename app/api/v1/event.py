from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from uuid import UUID

from sqlalchemy.orm import Session

from app.services.event_service import (
    create_event,
    add_attendee,
    get_event,
    list_events,
    join_event,
    leave_event,
    update_event,
    delete_event, list_my_events,
)
from app.schemas.schemas import (
    EventCreate,
    EventUpdate,
    EventRead,
    PaginatedEvents, EventTypeRead, EmployeeSummary,
)
from app.db.get_db import get_db

from app.models.models import Employers, EventEmployers, Events, EventTypes
from app.schemas.schemas import MessageDTO
from app.services.user_service import get_current_user, create_notification

router = APIRouter(prefix="/events", tags=["Events"])


@router.post("", response_model=EventRead)
async def create_new_event(
    event_in: EventCreate,
    db: Session = Depends(get_db),
    user_data: dict = Depends(get_current_user),
):
    owner_id = user_data["employee"].id_employee
    new_event = create_event(db, owner_id, event_in)
    db.commit()
    db.flush()

    unique_attendees = set(event_in.attendee_ids or [])
    for attendee_id in unique_attendees:
        emp_obj = db.query(Employers).filter_by(id_employee=attendee_id).first()
        if not emp_obj:
            raise HTTPException(
                status_code=400,
                detail=f"Сотрудник с ID {attendee_id} не найден"
            )

        db.add(EventEmployers(id_event=new_event.id_event, id_employee=attendee_id))
        db.commit()

        create_notification(db, f"Вы добавлены на мероприятие: {new_event.name_event}", [attendee_id])

    event_type_obj = db.query(EventTypes).filter_by(id_event_type=new_event.id_event_type).first()
    if not event_type_obj:
        raise HTTPException(status_code=404, detail="Тип события не найден")
    event_type_summary = EventTypeRead.from_orm(event_type_obj)

    owner_obj = db.query(Employers).filter_by(id_employee=new_event.id_owner).first()
    if not owner_obj:
        raise HTTPException(status_code=404, detail="Организатор не найден")
    owner_summary = EmployeeSummary.from_orm(owner_obj)

    attendees = (
        db.query(Employers)
            .join(EventEmployers, EventEmployers.id_employee == Employers.id_employee)
            .filter(EventEmployers.id_event == new_event.id_event)
            .all()
    )

    return EventRead.from_orm(
        new_event,
        attendees=attendees,
        owner_summary=owner_summary,
        event_type_summary=event_type_summary
    )


@router.get("", response_model=PaginatedEvents)
async def get_all_events(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1),
    search: Optional[str] = Query(None, description="Фильтр по названию, месту или типу"),
    db: Session = Depends(get_db),
):
    return list_events(db, skip=skip, limit=limit, search=search)


@router.get("/my", response_model=PaginatedEvents)
async def get_my_events(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1),
    search: Optional[str] = Query(None, description="Фильтр по названию, месту или типу"),
    db: Session = Depends(get_db),
    user_data: dict = Depends(get_current_user),
):
    employee_id = user_data["employee"].id_employee
    return list_my_events(db, employee_id, search=search, skip=skip, limit=limit)


@router.delete("/{event_id}/leave", response_model=MessageDTO)
async def leave_myself(
    event_id: UUID,
    db: Session = Depends(get_db),
    user_data: dict = Depends(get_current_user),
):
    leave_event(db, event_id, user_data["employee"].id_employee)
    db.commit()
    return MessageDTO(message="Вы отказались от участия в мероприятии")


@router.post("/{event_id}/attendees", response_model=MessageDTO)
async def add_person_to_event(
    event_id: UUID,
    employee_id: UUID = Query(..., description="ID сотрудника, которого добавляем"),
    db: Session = Depends(get_db),
    user_data: dict = Depends(get_current_user),
):
    event = db.query(Events).filter_by(id_event=event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Мероприятие не найдено")

    if event.id_owner != user_data["employee"].id_employee:
        raise HTTPException(status_code=403, detail="Нет прав добавлять сотрудников")

    add_attendee(db, event_id, employee_id)
    db.commit()

    create_notification(db, f"Вы добавлены на мероприятие: {event.name_event}", [employee_id])

    return MessageDTO(message="Сотрудник успешно добавлен в мероприятие")


@router.post("/{event_id}/join", response_model=MessageDTO)
async def join_myself(
    event_id: UUID,
    db: Session = Depends(get_db),
    user_data: dict = Depends(get_current_user),
):
    join_event(db, event_id, user_data["employee"].id_employee)
    db.commit()

    return MessageDTO(message="Вы успешно присоединились к мероприятию")


@router.put("/{event_id}", response_model=EventRead)
async def edit_my_event(
    event_id: UUID,
    event_in: EventUpdate,
    db: Session = Depends(get_db),
    user_data: dict = Depends(get_current_user),
):
    updated = update_event(db, event_id, event_in, user_data["employee"].id_employee)
    db.commit()
    attendees = (
        db.query(Employers)
        .join(EventEmployers, EventEmployers.id_employee == Employers.id_employee)
        .filter(EventEmployers.id_event == event_id)
        .all()
    )

    event_type_obj = db.query(EventTypes).filter_by(id_event_type=updated.id_event_type).first()
    if not event_type_obj:
        raise HTTPException(status_code=404, detail="Тип события не найден")
    event_type_summary = EventTypeRead.from_orm(event_type_obj)

    owner_obj = db.query(Employers).filter_by(id_employee=updated.id_owner).first()
    if not owner_obj:
        raise HTTPException(status_code=404, detail="Организатор не найден")
    owner_summary = EmployeeSummary.from_orm(owner_obj)

    return EventRead.from_orm(
        updated,
        attendees=attendees,
        owner_summary=owner_summary,
        event_type_summary=event_type_summary
    )


@router.delete("/{event_id}", response_model=MessageDTO)
async def delete_my_event(
    event_id: UUID,
    db: Session = Depends(get_db),
    user_data: dict = Depends(get_current_user),
):
    delete_event(db, event_id, user_data["employee"].id_employee)
    db.commit()
    return MessageDTO(message="Мероприятие успешно удалено")


@router.get("/{event_id}", response_model=EventRead)
async def get_one_event(
    event_id: UUID,
    db: Session = Depends(get_db),
):
    return get_event(db, event_id)
