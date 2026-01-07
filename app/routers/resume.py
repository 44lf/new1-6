import uuid
from fastapi import APIRouter, UploadFile, File, BackgroundTasks, HTTPException
from app.services.resume_service import ResumeService
from app.utils.minio_client import MinioClient
from app.settings import MINIO_BUCKET_NAME

router = APIRouter(prefix="/resumes", tags=["Resumes"])

@router.post("/upload", summary="上传简历PDF")
async def upload_resume(
    background_tasks: BackgroundTasks, 
    file: UploadFile = File(...)
):
    """
    上传简历 -> 保存到MinIO -> 创建数据库记录 -> 后台异步解析
    """
    # 1. 校验文件格式 (简单校验)
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="目前仅支持 PDF 文件上传")

    # 2. 生成唯一文件名，防止重名覆盖
    # 格式: resumes/uuid.pdf
    file_ext = file.filename.split(".")[-1]
    object_name = f"resumes/{uuid.uuid4()}.{file_ext}"

    try:
        # 3. 上传到 MinIO
        # 注意：这里需要你确保 MinioClient.upload_file 已经写好
        file_url = await MinioClient.upload_file(file, object_name)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件上传失败: {str(e)}")

    # 4. 创建数据库记录 (状态: Pending)
    resume = await ResumeService.create_resume_record(file_url=file_url)

    # 5. 【关键】添加后台任务，不阻塞当前接口返回
    background_tasks.add_task(ResumeService.process_resume_workflow, resume.id)

    return {
        "code": 200,
        "message": "上传成功，正在后台解析",
        "data": {
            "resume_id": resume.id,
            "file_url": file_url
        }
    }

@router.get("/{resume_id}", summary="查询简历状态")
async def get_resume_status(resume_id: int):
    # 这里简单直接查库，如果逻辑复杂建议也封装到 Service
    from app.db.resume_table import Resume
    resume = await Resume.get_or_none(id=resume_id)
    if not resume:
        raise HTTPException(status_code=404, detail="简历不存在")
    return resume