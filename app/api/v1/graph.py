from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.get_db import get_db
from app.models.models import *
from app.schemas.schemas import GraphViewDTO, GraphNode, GraphLink

router = APIRouter(prefix="/graph", tags=["graph"])


@router.get("/{graph_type}", response_model=GraphViewDTO)
def get_structure(graph_type: str, db: Session = Depends(get_db)):
    nodes = []
    links = []

    if graph_type == "departments":
        departments = db.query(Departments).all()
        employees = db.query(Employers).all()

        for d in departments:
            nodes.append(GraphNode(id=str(d.id_department), name=d.name_department, group="department"))

        for e in employees:
            eid = str(e.id_employee)
            full_name = f"{e.last_name} {e.first_name}"
            nodes.append(GraphNode(id=eid, name=full_name, group="employee"))
            links.append(GraphLink(source=str(e.id_department), target=eid))

    elif graph_type == "roles":
        roles = db.query(Roles).all()
        assignments = db.query(ProjectsEmployers).all()
        employees = {e.id_employee: e for e in db.query(Employers).all()}

        for r in roles:
            nodes.append(GraphNode(id=str(r.id_role), name=r.name_role, group="role"))

        for a in assignments:
            emp = employees.get(a.id_employee)
            if not emp:
                continue
            full_name = f"{emp.last_name} {emp.first_name}"
            nodes.append(GraphNode(id=str(emp.id_employee), name=full_name, group="employee"))
            links.append(GraphLink(source=str(a.id_role), target=str(emp.id_employee)))

    elif graph_type == "cities":
        employees = db.query(Employers).all()
        cities = set(e.city for e in employees)

        for city in cities:
            city_id = city.replace(" ", "_")
            nodes.append(GraphNode(id=city_id, name=city, group="city"))

        for e in employees:
            eid = str(e.id_employee)
            full_name = f"{e.last_name} {e.first_name}"
            city_id = e.city.replace(" ", "_")
            nodes.append(GraphNode(id=eid, name=full_name, group="employee"))
            links.append(GraphLink(source=city_id, target=eid))

    elif graph_type == "teams":
        projects = db.query(Projects).all()
        assignments = db.query(ProjectsEmployers).all()
        employees = {e.id_employee: e for e in db.query(Employers).all()}

        for p in projects:
            nodes.append(GraphNode(id=str(p.id_project), name=p.name_project, group="project"))

        for a in assignments:
            emp = employees.get(a.id_employee)
            if not emp:
                continue
            full_name = f"{emp.last_name} {emp.first_name}"
            eid = str(emp.id_employee)
            nodes.append(GraphNode(id=eid, name=full_name, group="employee"))
            links.append(GraphLink(source=str(a.id_project), target=eid))

    elif graph_type == "stacks":
        techs = db.query(Technologies).all()
        tech_map = {t.id_technology: t.name_technology for t in techs}
        assignments = db.query(TechnologyEmployee).all()
        employees = {e.id_employee: e for e in db.query(Employers).all()}

        for tid, name in tech_map.items():
            nodes.append(GraphNode(id=str(tid), name=name, group="tech"))

        for a in assignments:
            emp = employees.get(a.id_employee)
            if not emp:
                continue
            eid = str(emp.id_employee)
            full_name = f"{emp.last_name} {emp.first_name}"
            nodes.append(GraphNode(id=eid, name=full_name, group="employee"))
            links.append(GraphLink(source=str(a.id_technology), target=eid))

    elif graph_type == "interests":
        interests = db.query(Interests).all()
        interest_map = {i.id_interest: i.name_interest for i in interests}
        assignments = db.query(InterestsEmployers).all()
        employees = {e.id_employee: e for e in db.query(Employers).all()}

        for iid, name in interest_map.items():
            nodes.append(GraphNode(id=str(iid), name=name, group="interest"))

        for a in assignments:
            emp = employees.get(a.id_employee)
            if not emp:
                continue
            eid = str(emp.id_employee)
            full_name = f"{emp.last_name} {emp.first_name}"
            nodes.append(GraphNode(id=eid, name=full_name, group="employee"))
            links.append(GraphLink(source=str(a.id_interest), target=eid))

    else:
        raise HTTPException(status_code=400, detail="Некорректный тип графа")

    return GraphViewDTO(nodes=nodes, links=links)
