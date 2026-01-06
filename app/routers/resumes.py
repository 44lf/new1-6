from fastapi import APIRouter, BackgroundTasks, File, UploadFile

from app.models.resume import ResumeCreateResponse
from app.services.resume_service import ResumeService

router = APIRouter(prefix="/resumes", tags=["resumes"])


@router.post("/upload", response_model=ResumeCreateResponse, summary="上传简历")
async def upload_resume(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    prompt: str | None = None,
):
    service = ResumeService()
    return await service.upload_and_process(background_tasks, file, prompt)
