from app.models.models import Base


def create_tables(engine):
    Base.metadata.create_all(bind=engine)
