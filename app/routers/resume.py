import uuid
from datetime import datetime
from fastapi import APIRouter, UploadFile, File, BackgroundTasks, HTTPException, Query,Depends
from typing import Optional

from app.services.resume_service import ResumeService
from app.utils.minio_client import MinioClient
from app.db.resume_table import Resume
from app.prompts.base import BasePromptProvider
from app.prompts.resume_prompt_provider import ResumePromptProvider
from app.enums.education import SchoolTier, Degree


router = APIRouter(prefix="/resumes", tags=["Resumes"])

def get_prompt_provider() -> BasePromptProvider:
    return ResumePromptProvider()

@router.post("/upload", summary="上传简历PDF")
async def upload_resume(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    prompt_provider: BasePromptProvider = Depends(get_prompt_provider)
):

    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="目前仅支持 PDF 文件上传")

    ext = file.filename.split(".")[-1]
    object_name = f"resumes/{uuid.uuid4()}.{ext}"

    try:
        file_url = await MinioClient.upload_file(file, object_name)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件上传失败: {str(e)}")

    resume = await ResumeService.create_resume_record(file_url=file_url)
    await resume.refresh_from_db()

    background_tasks.add_task(
        ResumeService.process_resume_workflow,
        resume.id,
        prompt_provider
    )

    return {
        "code": 200,
        "message": "上传成功，正在后台解析",
        "data": {
            "resume_id": resume.id,
            "file_url": file_url,
        },
    }






@router.post("/{resume_id}/analyze", summary="重新分析单份简历")
async def resume_analyze(
    resume_id: int,
    background_tasks: BackgroundTasks,
    prompt_provider: BasePromptProvider = Depends(get_prompt_provider)
):
    resume = await Resume.get_or_none(id=resume_id)
    if not resume:
        raise HTTPException(status_code=404, detail="简历不存在")

    background_tasks.add_task(
        ResumeService.process_resume_workflow,
        resume.id,
        prompt_provider
    )

    return {"code": 200, "message": "已将简历重新加入解析队列"}

@router.post("/reanalyze/all", summary="一键重新筛选所有简历")
async def reanalyze_all_resumes(
    background_tasks: BackgroundTasks,
    prompt_provider: BasePromptProvider = Depends(get_prompt_provider) # 1. 注入依赖
):
    """
    **全量重新筛选**：
    当更换了 Prompt 后，点击此按钮。
    后台会用最新的提示词对库里所有简历重新进行 AI 评估。
    """
    all_ids = await ResumeService.get_all_resume_ids()

    if not all_ids:
        return {"code": 200, "message": "当前简历库为空，无需重测"}

    background_tasks.add_task(ResumeService.batch_reanalyze_resumes, all_ids,prompt_provider)

    return {
        "code": 200,
        "message": f"已触发全量重测任务，共 {len(all_ids)} 份简历正在后台重新排队解析...",
    }

@router.get("/", summary="多维度搜索简历")
async def list_resumes(
    status: Optional[int] = Query(None, description="状态(0=未处理, 1=处理中, 2=合格, 3=不合格)"),
    is_qualified: Optional[bool] = Query(None, description="筛选合格/不合格"),
    name: Optional[str] = Query(None, description="搜索姓名"),
    university: Optional[str] = Query(None, description="搜索学校"),
    major: Optional[str] = Query(None, description="搜索专业"),
    skill: Optional[str] = Query(None, description="搜索技能 (如: Python)"),
    schooltier: Optional[SchoolTier] = Query(None, description="学校层次"),
    degree: Optional[Degree] = Query(None, description='学历层次'),
    date_from: Optional[datetime] = Query(None, description="起始日期/时间 (>=)"),
    date_to: Optional[datetime] = Query(None, description="结束日期/时间 (<=)"),
):
    return await ResumeService.get_resumes(
        status=status,
        is_qualified=is_qualified,
        name=name,
        university=university,
        major=major,
        skill=skill,
        schooltier=schooltier,
        degree=degree,
        date_from=date_from,
        date_to=date_to,
    )

@router.delete("/", summary="根据信息删除简历")
async def delete_resume_by_info(
    name: Optional[str] = Query(None, description="按姓名删除"),
    email: Optional[str] = Query(None, description="按邮箱删除"),
    phone: Optional[str] = Query(None, description="按电话删除")
):
    if not any([name, email, phone]):
        raise HTTPException(status_code=400, detail="请至少提供姓名、邮箱或电话中的一项")

    deleted_count = await ResumeService.delete_resumes_by_info(name, email, phone)

    if deleted_count == 0:
        raise HTTPException(status_code=404, detail="未找到符合条件的简历")

    return {"message": f"成功删除了 {deleted_count} 份简历记录"}
