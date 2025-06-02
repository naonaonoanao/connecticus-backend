from math import ceil
from typing import List
from uuid import UUID

from sqlalchemy import or_
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.models.models import (
    Events,
    EventEmployers,
    Employers, EventTypes,
)
from app.schemas.schemas import (
    EventCreate,
    EventUpdate,
    EventRead,
    PaginatedEvents,
    EmployeeSummary, EventTypeRead,
)


def create_event(db: Session, owner_id: UUID, event_in: EventCreate) -> Events:
    new_event = Events(
        name_event=event_in.name_event.strip(),
        date=event_in.date,
        place=event_in.place.strip(),
        id_owner=owner_id,
        id_event_type=event_in.id_event_type,
    )
    db.add(new_event)
    db.flush()  # чтобы получить new_event.id_event
    return new_event


def add_attendee(db: Session, event_id: UUID, employee_id: UUID):
    # Проверим, что событие существует
    event = db.query(Events).filter_by(id_event=event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Событие не найдено")

    # Проверим, что сотрудник существует
    emp = db.query(Employers).filter_by(id_employee=employee_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Сотрудник не найден")

    # Проверим, нет ли уже связи
    exists = db.query(EventEmployers).filter_by(
        id_event=event_id, id_employee=employee_id
    ).first()
    if exists:
        raise HTTPException(status_code=400, detail="Сотрудник уже добавлен в мероприятие")

    link = EventEmployers(id_event=event_id, id_employee=employee_id)
    db.add(link)


def remove_attendee(db: Session, event_id: UUID, employee_id: UUID):
    link = db.query(EventEmployers).filter_by(
        id_event=event_id, id_employee=employee_id
    ).first()
    if not link:
        raise HTTPException(status_code=404, detail="Сотрудник не участвует в этом мероприятии")
    db.delete(link)


def get_event(db: Session, event_id: UUID) -> EventRead:
    # 1) Получаем само мероприятие
    event = db.query(Events).filter_by(id_event=event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Мероприятие не найдено")

    # 2) Собираем участников – но сразу конвертируем в EmployeeSummary
    employer_objs = (
        db.query(Employers)
        .join(EventEmployers, EventEmployers.id_employee == Employers.id_employee)
        .filter(EventEmployers.id_event == event_id)
        .all()
    )
    attendees_summaries = [EmployeeSummary.from_orm(emp) for emp in employer_objs]
    event_type_obj = db.query(EventTypes).filter_by(id_event_type=event.id_event_type).first()
    if not event_type_obj:
        raise HTTPException(status_code=404, detail="Тип события не найден")
    event_type_summary = EventTypeRead.from_orm(event_type_obj)

    owner_obj = db.query(Employers).filter_by(id_employee=event.id_owner).first()
    if not owner_obj:
        raise HTTPException(status_code=404, detail="Организатор не найден")
    owner_summary = EmployeeSummary.from_orm(owner_obj)

    return EventRead.from_orm(
        event,
        attendees=attendees_summaries,
        event_type_summary=event_type_summary,
        owner_summary=owner_summary
    )


def list_events(
    db: Session, search: str, skip: int = 0, limit: int = 10
) -> PaginatedEvents:
    query = db.query(Events).join(EventTypes, Events.id_event_type == EventTypes.id_event_type)

    if search:
        pattern = f"%{search.lower()}%"
        query = query.filter(
            or_(
                Events.name_event.ilike(pattern),
                Events.place.ilike(pattern),
                EventTypes.name_type.ilike(pattern)
            )
        )

    total = db.query(Events).count()
    events = (
        query
        .order_by(Events.date.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    result: List[EventRead] = []
    for ev in events:
        employer_objs = (
            db.query(Employers)
            .join(EventEmployers, EventEmployers.id_employee == Employers.id_employee)
            .filter(EventEmployers.id_event == ev.id_event)
            .all()
        )
        attendees_summaries = [EmployeeSummary.from_orm(emp) for emp in employer_objs]

        event_type_obj = db.query(EventTypes).filter_by(id_event_type=ev.id_event_type).first()
        if not event_type_obj:
            raise HTTPException(status_code=404, detail="Тип события не найден")
        event_type_summary = EventTypeRead.from_orm(event_type_obj)

        owner_obj = db.query(Employers).filter_by(id_employee=ev.id_owner).first()
        if not owner_obj:
            raise HTTPException(status_code=404, detail="Организатор не найден")
        owner_summary = EmployeeSummary.from_orm(owner_obj)

        result.append(
            EventRead.from_orm(
                ev,
                attendees=attendees_summaries,
                event_type_summary=event_type_summary,
                owner_summary=owner_summary
            )
        )

    return PaginatedEvents(
        total_count=total,
        total_pages=ceil(total/limit),
        skip=skip,
        limit=limit,
        events=result
    )


def list_my_events(
    db: Session,
    employee_id: UUID,
    search: str,
    skip: int = 0,
    limit: int = 10
) -> PaginatedEvents:
    q = db.query(Events).join(EventTypes, Events.id_event_type == EventTypes.id_event_type)

    if search:
        pattern = f"%{search.lower()}%"
        q = q.filter(
            or_(
                Events.name_event.ilike(pattern),
                Events.place.ilike(pattern),
                EventTypes.name_type.ilike(pattern)
            )
        )

    subq = (
        db.query(EventEmployers.id_event)
          .filter(EventEmployers.id_employee == employee_id)
          .subquery()
    )

    query = (
        q
        .filter(
          or_(
              Events.id_owner == employee_id,
              Events.id_event.in_(subq)
          )
        )
    )

    total = query.count()
    events = (
        query
        .order_by(Events.date.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    result: List[EventRead] = []
    for ev in events:
        employer_objs = (
            db.query(Employers)
              .join(EventEmployers, EventEmployers.id_employee == Employers.id_employee)
              .filter(EventEmployers.id_event == ev.id_event)
              .all()
        )
        attendees_summaries = [EmployeeSummary.from_orm(emp) for emp in employer_objs]

        event_type_obj = db.query(EventTypes).filter_by(id_event_type=ev.id_event_type).first()
        if not event_type_obj:
            raise HTTPException(status_code=404, detail="Тип события не найден")
        event_type_summary = EventTypeRead.from_orm(event_type_obj)

        owner_obj = db.query(Employers).filter_by(id_employee=ev.id_owner).first()
        if not owner_obj:
            raise HTTPException(status_code=404, detail="Организатор не найден")
        owner_summary = EmployeeSummary.from_orm(owner_obj)

        result.append(
            EventRead.from_orm(
                ev,
                attendees=attendees_summaries,
                event_type_summary=event_type_summary,
                owner_summary=owner_summary
            )
        )

    return PaginatedEvents(
        total_count=total,
        total_pages=ceil(total/limit),
        skip=skip,
        limit=limit,
        events=result
    )


def join_event(db: Session, event_id: UUID, employee_id: UUID):
    # Проверим, что событие существует
    event = db.query(Events).filter_by(id_event=event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Мероприятие не найдено")

    exists = db.query(EventEmployers).filter_by(
        id_event=event_id, id_employee=employee_id
    ).first()
    if exists:
        raise HTTPException(status_code=400, detail="Вы уже участвуете в этом мероприятии")

    link = EventEmployers(id_event=event_id, id_employee=employee_id)
    db.add(link)


def leave_event(db: Session, event_id: UUID, employee_id: UUID):
    link = db.query(EventEmployers).filter_by(
        id_event=event_id, id_employee=employee_id
    ).first()
    if not link:
        raise HTTPException(status_code=400, detail="Вы не участвуете в этом мероприятии")
    db.delete(link)


def update_event(
    db: Session, event_id: UUID, event_in: EventUpdate, current_user_id: UUID
) -> Events:
    event = db.query(Events).filter_by(id_event=event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Мероприятие не найдено")

    if event.id_owner != current_user_id:
        raise HTTPException(status_code=403, detail="Нет прав для редактирования этого мероприятия")

    # Обновляем поля
    event.name_event = event_in.name_event.strip()
    event.date = event_in.date
    event.place = event_in.place.strip()
    event.id_event_type = event_in.id_event_type

    db.flush()
    return event


def delete_event(db: Session, event_id: UUID, current_user_id: UUID):
    event = db.query(Events).filter_by(id_event=event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Мероприятие не найдено")

    if event.id_owner != current_user_id:
        raise HTTPException(status_code=403, detail="Нет прав для удаления этого мероприятия")

    # Сначала удалим связи
    db.query(EventEmployers).filter_by(id_event=event_id).delete()
    # Затем само мероприятие
    db.delete(event)
