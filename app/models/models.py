import uuid
from datetime import datetime

from sqlalchemy import (
    Column,
    String,
    Date,
    ForeignKey,
    DateTime,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class Interests(Base):
    __tablename__ = "interests"

    pk_interest = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name_interest = Column(String(25), nullable=False)


class Employees(Base):
    __tablename__ = "employees"

    pk_employee = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    telegram_name = Column(String(25), nullable=False)
    join_date = Column(Date, nullable=True)
    full_name = Column(String(25), nullable=False)

    user = relationship("Users", uselist=False, back_populates="employee")


class InterestedEmployers(Base):
    __tablename__ = "interested_employers"
    pk_interest = Column(UUID(as_uuid=True), ForeignKey("interests.pk_interest"), primary_key=True)
    pk_employee = Column(UUID(as_uuid=True), ForeignKey("employees.pk_employee"), primary_key=True)


class Events(Base):
    __tablename__ = "events"

    pk_event = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pk_project = Column(UUID(as_uuid=True), ForeignKey("projects.pk_project"))
    name_event = Column(String(25), nullable=False)


class EventEmployers(Base):
    __tablename__ = "event_employers"
    pk_event = Column(UUID(as_uuid=True), ForeignKey("events.pk_event"), primary_key=True)
    pk_employee = Column(UUID(as_uuid=True), ForeignKey("employees.pk_employee"), primary_key=True)


class EventTypes(Base):
    __tablename__ = "event_types"

    pk_type = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name_type = Column(String(25), nullable=False)


class Departments(Base):
    __tablename__ = "departments"

    pk_department = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name_department = Column(String(25), nullable=False)


class Projects(Base):
    __tablename__ = "projects"

    pk_project = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name_project = Column(String(25), nullable=False)
    description = Column(String(25), nullable=True)


class ProjectsEmployers(Base):
    __tablename__ = "projects_employers"
    pk_department = Column(UUID(as_uuid=True), ForeignKey("departments.pk_department"), primary_key=True)
    pk_employee = Column(UUID(as_uuid=True), ForeignKey("employees.pk_employee"), primary_key=True)
    pk_project = Column(UUID(as_uuid=True), ForeignKey("projects.pk_project"), primary_key=True)


class Roles(Base):
    __tablename__ = "roles"

    pk_role = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name_role = Column(String(25), nullable=False)


class Technologies(Base):
    __tablename__ = "technologies"

    pk_technology = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name_technology = Column(String(25), nullable=False)


class TechnologiesProjects(Base):
    __tablename__ = "technologies_projects"

    pk_technology = Column(UUID(as_uuid=True), ForeignKey("technologies.pk_technology"), primary_key=True)
    pk_project = Column(UUID(as_uuid=True), ForeignKey("projects.pk_project"), primary_key=True)


class Ranks(Base):
    __tablename__ = "ranks"

    pk_rank = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name_rank = Column(String(25), nullable=False)


class TechnologyEmployee(Base):
    __tablename__ = "technology_employee"

    pk_technology = Column(UUID(as_uuid=True), ForeignKey("technologies.pk_technology"), primary_key=True)
    pk_employee = Column(UUID(as_uuid=True), ForeignKey("employees.pk_employee"), primary_key=True)


class Positions(Base):
    __tablename__ = "positions"

    pk_position = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    position_name = Column(String(25), nullable=False)


class PositionsEmployers(Base):
    __tablename__ = "positions_employers"

    pk_position = Column(UUID(as_uuid=True), ForeignKey("positions.pk_position"), primary_key=True)
    pk_employee = Column(UUID(as_uuid=True), ForeignKey("employees.pk_employee"), primary_key=True)


class Users(Base):
    __tablename__ = "users"
    username = Column(String(50), primary_key=True, index=True)
    hashed_password = Column(String(128), nullable=False)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("employees.pk_employee"), nullable=False)

    employee = relationship("Employees", back_populates="user")
