import uvicorn
from fastapi import FastAPI

from app.db import models
from app.db.database import engine
from app.routers import resumes

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Resume Screening Backend")
app.include_router(resumes.router)


@app.get("/", tags=["health"])
async def health() -> dict:
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
