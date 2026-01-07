import uuid
from fastapi import APIRouter, UploadFile, File, BackgroundTasks, HTTPException, Query
from typing import Optional
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
    await resume.refresh_from_db()

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
@router.get("/", summary="多维度搜索简历")
async def list_resumes(
    status: Optional[int] = Query(None, description="状态(0=未处理, 1=处理中, 2=合格, 3=不合格)"),
    is_qualified: Optional[bool] = Query(None, description="筛选合格/不合格"),
    name: Optional[str] = Query(None, description="搜索姓名"),
    university: Optional[str] = Query(None, description="搜索学校"),
    major: Optional[str] = Query(None, description="搜索专业"),
    skill: Optional[str] = Query(None, description="搜索技能 (如: Python)"),
):
    """
    **超级简历查询**：
    支持组合查询，例如：
    - "查看所有合格的简历" (`is_qualified=true`)
    - "查看所有清华大学的简历" (`university=清华`)
    - "查看未处理且技能包含 Python 的简历" (`status=0&skill=Python`)
    """
    return await ResumeService.get_resumes(
        status=status,
        is_qualified=is_qualified,
        name=name,
        university=university,
        major=major,
        skill=skill
    )

@router.delete("/", summary="根据信息删除简历")
async def delete_resume_by_info(
    name: Optional[str] = Query(None, description="按姓名删除"),
    email: Optional[str] = Query(None, description="按邮箱删除"),
    phone: Optional[str] = Query(None, description="按电话删除")
):
    """
    **简历清理**：
    不需要 ID，直接根据解析出来的姓名、邮箱或电话删除记录。
    通常用于清理测试数据或移除特定候选人。
    """
    if not any([name, email, phone]):
        raise HTTPException(status_code=400, detail="请至少提供姓名、邮箱或电话中的一项")

    deleted_count = await ResumeService.delete_resumes_by_info(name, email, phone)

    if deleted_count == 0:
        raise HTTPException(status_code=404, detail="未找到符合条件的简历")

    return {"message": f"成功删除了 {deleted_count} 份简历记录"}
