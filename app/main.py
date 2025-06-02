from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware

load_dotenv()

from app.core.config import settings
from fastapi import FastAPI
from app.core.database import engine
from app.api.v1 import employee, user, graph, common, event
from fastapi import APIRouter

from app.db.create_tables import create_tables
from app.db.seed_data import seed_data


def get_application() -> FastAPI:
    create_tables(engine)
    seed_data(engine)
    app = FastAPI(
        title="My Basic FastAPI App",
        version="1.0.0",
    )
    v1_router = APIRouter(prefix='/api/v1')
    v1_router.include_router(employee.router)
    v1_router.include_router(user.router)
    v1_router.include_router(graph.router)
    v1_router.include_router(common.router)
    v1_router.include_router(event.router)

    app.include_router(v1_router)

    origins = ["*"]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    return app


app = get_application()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=settings.PORT, reload=True)
