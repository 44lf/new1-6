import uvicorn
from fastapi import FastAPI

from app.config import settings
from app.db.database import register_db
from app.routers import resumes

app = FastAPI(title=settings.app_name)
register_db(app)
app.include_router(resumes.router)


@app.get("/", tags=["health"])
async def health() -> dict:
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
