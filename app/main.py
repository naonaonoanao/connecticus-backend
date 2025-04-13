from dotenv import load_dotenv

load_dotenv()

from app.core.config import settings
from fastapi import FastAPI
from app.core.database import engine
from app.api.v1 import employee, user
from fastapi import APIRouter

from app.db.create_tables import create_tables


def get_application() -> FastAPI:
    create_tables(engine)
    app = FastAPI(
        title="My Basic FastAPI App",
        version="1.0.0",
    )
    v1_router = APIRouter(prefix='/api/v1')
    v1_router.include_router(employee.router)
    v1_router.include_router(user.router)

    app.include_router(v1_router)

    return app


app = get_application()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=settings.PORT, reload=True)
