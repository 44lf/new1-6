<<<<<<< ours
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings

engine = create_engine(settings.database_url, future=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, future=True)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
=======
from tortoise.contrib.fastapi import register_tortoise

from app.config import settings


def register_db(app) -> None:
    register_tortoise(
        app,
        db_url=settings.database_url,
        modules={"models": ["app.db.models"]},
        generate_schemas=True,
        add_exception_handlers=True,
    )
>>>>>>> theirs
