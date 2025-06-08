from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import distinct

from app.db.get_db import get_db
from app.models.models import (
    Employers,
    Positions,
    Departments,
    Projects,
    Technologies,
    Interests, NotificationsEmployees, Notifications,
)
from app.schemas.schemas import PositionRead, DepartmentRead, TechnologyRead, InterestsRead, ProjectRead, \
    TechnologySoloRead, NotificationReadRequest, NotificationOut
from app.services.user_service import get_current_user

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


@router.get(
    "/notifications",
    response_model=List[NotificationOut],
    summary="Получить все уведомления для сотрудника (с флагом прочитано/непрочитано)"
)
async def get_notifications_for_employee(
    user_data: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Возвращает список всех уведомлений конкретного сотрудника.
    Для каждого уведомления возвращаются:
      - id (UUID)
      - content (строка)
      - is_shown (булево — прочитано/нет)
    """
    exists_emp = db.query(Employers).filter(Employers.id_employee == user_data["employee"].id_employee).first()
    if not exists_emp:
        raise HTTPException(status_code=404, detail="Employee not found")

    rows = (
        db.query(Notifications, NotificationsEmployees.is_shown)
          .join(
              NotificationsEmployees,
              Notifications.id == NotificationsEmployees.id_notification
          )
          .filter(NotificationsEmployees.id_employee == user_data["employee"].id_employee)
          .order_by(Notifications.id)
          .all()
    )

    result: List[NotificationOut] = []
    for notif, is_shown in rows:
        result.append(
            NotificationOut(
                id=notif.id,
                content=notif.content,
                is_shown=is_shown
            )
        )
    return result


@router.post(
    "/notifications/read",
    summary="Отметить список уведомлений как прочитанных для конкретного сотрудника"
)
async def mark_notifications_as_read(
    payload: NotificationReadRequest,
    user_data: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    payload: {
      "employee_id": UUID,
      "notification_ids": [UUID, UUID, ...]
    }
    Отмечаем все записи NotificationsEmployees.is_shown = True
    для заданного employee_id и списка notification_ids.
    """
    exists_emp = db.query(Employers).filter(Employers.id_employee == user_data["employee"].id_employee).first()
    if not exists_emp:
        raise HTTPException(status_code=404, detail="Employee not found")

    assocs = (
        db.query(NotificationsEmployees)
          .filter(
              NotificationsEmployees.id_employee == user_data["employee"].id_employee,
              NotificationsEmployees.id_notification.in_(payload.notification_ids)
          )
          .all()
    )

    if not assocs:
        return {"updated": 0}

    for assoc in assocs:
        assoc.is_shown = True

    db.commit()
    return {"updated": len(assocs)}
