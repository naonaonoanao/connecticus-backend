import uuid

from sqlalchemy import (
    Column,
    String,
    Date,
    ForeignKey,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class Interests(Base):
    __tablename__ = "interests"

    id_interest = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name_interest = Column(String(52), nullable=False)


class Employers(Base):
    __tablename__ = "employers"

    id_employee = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    first_name = Column(String(52), nullable=False)
    last_name = Column(String(52), nullable=False)
    middle_name = Column(String(52), nullable=True)
    date_of_birth = Column(Date, nullable=False)
    email = Column(String(150), nullable=False)
    phone_number = Column(String(18), nullable=False)
    telegram_name = Column(String(25), nullable=False)
    city = Column(String(52), nullable=False)
    id_position = Column(UUID(as_uuid=True), ForeignKey("positions.id_position"))
    id_department = Column(UUID(as_uuid=True), ForeignKey("departments.id_department"))

    user = relationship("Users", uselist=False, back_populates="employee")


class InterestsEmployers(Base):
    __tablename__ = "interests_employers"
    id_interest = Column(UUID(as_uuid=True), ForeignKey("interests.id_interest"), primary_key=True)
    id_employee = Column(UUID(as_uuid=True), ForeignKey("employers.id_employee"), primary_key=True)


class Events(Base):
    __tablename__ = "events"

    id_event = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name_event = Column(String(52), nullable=False)
    date = Column(Date, nullable=False)
    place = Column(String(52), nullable=False)
    id_owner = Column(UUID(as_uuid=True), ForeignKey("employers.id_employee"))
    id_event_type = Column(UUID(as_uuid=True), ForeignKey("event_types.id_event_type"))


class EventEmployers(Base):
    __tablename__ = "event_employers"
    id_event = Column(UUID(as_uuid=True), ForeignKey("events.id_event"), primary_key=True)
    id_employee = Column(UUID(as_uuid=True), ForeignKey("employers.id_employee"), primary_key=True)


class EventTypes(Base):
    __tablename__ = "event_types"

    id_event_type = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name_type = Column(String(52), nullable=False)


class Departments(Base):
    __tablename__ = "departments"

    id_department = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name_department = Column(String(52), nullable=False)


class Projects(Base):
    __tablename__ = "projects"

    id_project = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name_project = Column(String(52), nullable=False)
    description = Column(String(52), nullable=True)


class ProjectsEmployers(Base):
    __tablename__ = "projects_employers"
    id_role = Column(UUID(as_uuid=True), ForeignKey("roles.id_role"), primary_key=True)
    id_employee = Column(UUID(as_uuid=True), ForeignKey("employers.id_employee"), primary_key=True)
    id_project = Column(UUID(as_uuid=True), ForeignKey("projects.id_project"), primary_key=True)


class Roles(Base):
    __tablename__ = "roles"

    id_role = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name_role = Column(String(52), nullable=False)
    description = Column(String(52), nullable=False)


class Technologies(Base):
    __tablename__ = "technologies"

    id_technology = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name_technology = Column(String(52), nullable=False)
    description = Column(String(52), nullable=False)


class TechnologiesProjects(Base):
    __tablename__ = "technologies_projects"

    id_technology = Column(UUID(as_uuid=True), ForeignKey("technologies.id_technology"), primary_key=True)
    id_project = Column(UUID(as_uuid=True), ForeignKey("projects.id_project"), primary_key=True)


class Ranks(Base):
    __tablename__ = "ranks"

    id_rank = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name_rank = Column(String(52), nullable=False)


class TechnologyEmployee(Base):
    __tablename__ = "technology_employers"

    id_technology = Column(UUID(as_uuid=True), ForeignKey("technologies.id_technology"), primary_key=True)
    id_employee = Column(UUID(as_uuid=True), ForeignKey("employers.id_employee"), primary_key=True)
    id_rank = Column(UUID(as_uuid=True), ForeignKey("ranks.id_rank"))


class Positions(Base):
    __tablename__ = "positions"

    id_position = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    position_name = Column(String(52), nullable=False)


class Users(Base):
    __tablename__ = "users"
    username = Column(String(50), primary_key=True, index=True)
    hashed_password = Column(String(128), nullable=False)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("employers.id_employee"), nullable=False)
    role_id = Column(UUID(as_uuid=True), ForeignKey("system_roles.id_role"), nullable=False)

    employee = relationship("Employers", back_populates="user")


class SystemRoles(Base):
    __tablename__ = "system_roles"
    id_role = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    role_name = Column(String(20), nullable=False)

