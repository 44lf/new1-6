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
