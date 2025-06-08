import random
from datetime import date
from sqlalchemy.orm import Session
from app.models.models import (
    Departments, Employers, Positions, Projects, ProjectsEmployers,
    Interests, InterestsEmployers, Technologies, TechnologyEmployee,
    Ranks, Roles, EventTypes, Events, EventEmployers, Users, SystemRoles
)
from mimesis import Person, Internet, Datetime, Address
from mimesis.enums import Gender
from mimesis.locales import Locale

from app.services.user_service import get_password_hash

person = Person(locale=Locale.RU)
internet = Internet()
dt = Datetime(locale=Locale.RU)
ru = Address(locale=Locale.RU)

employees = []


def seed_data(engine):
    session = Session(bind=engine)

    # Проверяем, пуста ли таблица Users
    users_count = session.query(Users).count()
    if users_count > 0:
        print(f"Таблица Users не пуста (найдено {users_count} пользователей). Сеид инг пропущен.")
        return

    # Departments
    departments = [
        Departments(name_department="Разработка"),
        Departments(name_department="Аналитика"),
        Departments(name_department="Инфо без")
    ]
    session.add_all(departments)
    session.flush()

    # Positions
    positions = [
        Positions(position_name="Аналитик технологических процессов"),
        Positions(position_name="Специалист по ИБ"),
        Positions(position_name="Менеджер по отделу кадров"),
        Positions(position_name="Средний инженер-программист"),
        Positions(position_name="Старший инженер-программист"),
        Positions(position_name="Младший инженер-программист")
    ]
    session.add_all(positions)
    session.flush()

    # System roles
    system_roles = [
        SystemRoles(role_name="Администратор"),
        SystemRoles(role_name="Сотрудник"),
        SystemRoles(role_name="HR")
    ]
    session.add_all(system_roles)
    session.flush()

    # Ranks
    ranks = [
        Ranks(name_rank="Junior"),
        Ranks(name_rank="Middle"),
        Ranks(name_rank="Senior")
    ]
    session.add_all(ranks)
    session.flush()

    # Roles
    roles = [
        Roles(name_role="Full-stack разработчик", description="Полный доступ"),
        Roles(name_role="Прожект менеджер", description="Ограниченный доступ"),
        Roles(name_role="Тим лид", description="Ограниченный доступ"),
        Roles(name_role="Backend разработчик", description="Ограниченный доступ"),
        Roles(name_role="Frontend разработчик", description="Ограниченный доступ"),
        Roles(name_role="Системный аналитик", description="Ограниченный доступ"),
        Roles(name_role="Бизнес-аналитик", description="Ограниченный доступ"),
        Roles(name_role="Специалист по ИБ", description="Ограниченный доступ"),
        Roles(name_role="Мобильный разработчик", description="Ограниченный доступ"),
        Roles(name_role="Тестировщик", description="Ограниченный доступ")
    ]
    session.add_all(roles)
    session.flush()

    # Interests
    interests = [
        Interests(name_interest="Кибербезопасность"),
        Interests(name_interest="Искусственный интеллект"),
        Interests(name_interest="Разработка ПО"),
        Interests(name_interest="Музыка"),
        Interests(name_interest="Аниме")
    ]
    session.add_all(interests)
    session.flush()

    # Technologies
    technologies = [
        Technologies(name_technology="Python", description="Язык программирования"),
        Technologies(name_technology="PostgresSQL", description="База данных"),
        Technologies(name_technology="Docker", description="Контейнеризация"),
    ]
    session.add_all(technologies)
    session.flush()

    # Projects
    projects = [
        Projects(name_project="Внутренняя CRM", description="Система для работы с клиентами"),
        Projects(name_project="Система мониторинга ИБ", description="Отслеживание событий безопасности")
    ]
    session.add_all(projects)
    session.flush()

    # Генерация сотрудников со случайным отделом и позицией
    for i in range(60):
        department = random.choice(departments)
        pos = random.choice(positions)

        gender = Gender.MALE if i % 2 == 0 else Gender.FEMALE
        first_name = person.first_name(gender=gender)
        last_name = person.last_name(gender=gender)
        middle_name = person.surname(gender=gender)
        birth_year = dt.year(minimum=1930, maximum=2010)
        birth_month = random.randint(1, 12)
        birth_day = random.randint(1, 27)
        dob = date(birth_year, birth_month, birth_day)

        email = person.email()
        phone = person.phone_number(mask='+7 (9##) ###-##-##')
        telegram = person.username()

        emp = Employers(
            first_name=first_name,
            last_name=last_name,
            middle_name=middle_name,
            date_of_birth=dob,
            email=email,
            phone_number=phone,
            telegram_name=telegram,
            city=ru.city(),
            id_position=pos.id_position,
            id_department=department.id_department
        )
        employees.append(emp)

    session.add_all(employees)
    session.flush()

    # Привязки интересов, проектов и технологий
    for idx, emp in enumerate(employees):
        session.add(InterestsEmployers(
            id_employee=emp.id_employee,
            id_interest=interests[idx % len(interests)].id_interest
        ))
        session.add(ProjectsEmployers(
            id_employee=emp.id_employee,
            id_role=roles[idx % len(roles)].id_role,
            id_project=projects[idx % len(projects)].id_project
        ))
        session.add(TechnologyEmployee(
            id_employee=emp.id_employee,
            id_technology=technologies[idx % len(technologies)].id_technology,
            id_rank=ranks[idx % len(ranks)].id_rank
        ))

    # Event types и мероприятия
    event_types = [
        EventTypes(name_type="Внутреннее совещание"),
        EventTypes(name_type="Корпоратив")
    ]
    session.add_all(event_types)
    session.flush()

    event1 = Events(
        name_event="Встреча по проекту CRM",
        date=date(2025, 6, 1),
        place="Конференц-зал 1",
        id_owner=employees[0].id_employee,
        id_event_type=event_types[0].id_event_type
    )
    session.add(event1)
    session.flush()

    for i in range(5):
        session.add(EventEmployers(
            id_event=event1.id_event,
            id_employee=employees[i].id_employee
        ))

    # Пользователи
    for emp in employees:
        session.add(Users(
            username=f"user_{emp.id_employee.hex[:8]}",
            hashed_password=get_password_hash("password"),
            employee_id=emp.id_employee,
            role_id=system_roles[1].id_role
        ))

    session.commit()
    print("Данные успешно добавлены.")
