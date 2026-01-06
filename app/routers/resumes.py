<<<<<<< ours
from fastapi import APIRouter, BackgroundTasks, Depends, File, UploadFile

from app.db.database import get_db
=======
from fastapi import APIRouter, BackgroundTasks, File, UploadFile

>>>>>>> theirs
from app.models.resume import ResumeCreateResponse
from app.services.resume_service import ResumeService

router = APIRouter(prefix="/resumes", tags=["resumes"])


@router.post("/upload", response_model=ResumeCreateResponse, summary="上传简历")
async def upload_resume(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    prompt: str | None = None,
<<<<<<< ours
    db=Depends(get_db),
):
    service = ResumeService(db)
=======
):
    service = ResumeService()
>>>>>>> theirs
    return await service.upload_and_process(background_tasks, file, prompt)
