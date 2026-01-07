import uuid
from fastapi import APIRouter, UploadFile, File, BackgroundTasks, HTTPException

from app.services.resume_service import ResumeService
from app.utils.minio_client import MinioClient
from app.db.resume_table import Resume

router = APIRouter(prefix="/resumes", tags=["Resumes"])


@router.post("/upload", summary="上传简历PDF")
async def upload_resume(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    # 1. 校验文件格式
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="目前仅支持 PDF 文件上传")

    # 2. 生成唯一文件名
    ext = file.filename.split(".")[-1]
    object_name = f"resumes/{uuid.uuid4()}.{ext}"

    try:
        file_url = await MinioClient.upload_file(file, object_name)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件上传失败: {str(e)}")

    # 3. 创建简历记录
    resume = await ResumeService.create_resume_record(file_url=file_url)

    # ✅ 关键修复：确保数据已提交（非常重要）
    await resume.fetch_from_db()

    # 4. 添加后台解析任务
    background_tasks.add_task(
        ResumeService.process_resume_workflow,
        resume.id
    )

    return {
        "code": 200,
        "message": "上传成功，正在后台解析",
        "data": {
            "resume_id": resume.id,
            "file_url": file_url,
        },
    }


@router.post("/{resume_id}/analyze", summary="重新分析简历")
async def resume_analyze(
    resume_id: int,
    background_tasks: BackgroundTasks
):
    resume = await Resume.get_or_none(id=resume_id)
    if not resume:
        raise HTTPException(status_code=404, detail="简历不存在")

    background_tasks.add_task(
        ResumeService.process_resume_workflow,
        resume.id
    )

    return {
        "code": 200,
        "message": "已将简历重新加入解析队列",
    }
