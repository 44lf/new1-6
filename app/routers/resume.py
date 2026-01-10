# app/routers/resume.py - 优化版（代码量减少约 30%）
import uuid
from fastapi import APIRouter, UploadFile, File, BackgroundTasks, HTTPException, Query
from app.services.resume_service import ResumeService
from app.utils.minio_client import MinioClient
from app.db.resume_table import Resume

router = APIRouter(prefix="/resumes", tags=["Resumes"])


@router.post("/upload")
async def upload_resume(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    """上传简历"""
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(400, "仅支持 PDF 文件")

    object_name = f"resumes/{uuid.uuid4()}.pdf"

    try:
        file_url = await MinioClient.upload_file(file, object_name)
    except Exception as e:
        raise HTTPException(500, f"上传失败: {e}")

    resume = await ResumeService.create_resume_record(file_url)
    background_tasks.add_task(ResumeService.process_resume_workflow, resume.id)

    return {
        "code": 200,
        "message": "上传成功，正在后台解析",
        "data": {"resume_id": resume.id, "file_url": file_url},
    }


@router.post("/{resume_id}/analyze")
async def reanalyze_one(resume_id: int, background_tasks: BackgroundTasks):
    """重新分析单份简历"""
    resume = await Resume.get_or_none(id=resume_id)
    if not resume:
        raise HTTPException(404, "简历不存在")

    background_tasks.add_task(ResumeService.process_resume_workflow, resume.id)
    return {"code": 200, "message": "已重新加入解析队列"}


@router.post("/reanalyze/all")
async def reanalyze_all(background_tasks: BackgroundTasks):
    """批量重新筛选所有简历"""
    ids = await ResumeService.get_all_resume_ids()
    if not ids:
        return {"code": 200, "message": "简历库为空"}

    background_tasks.add_task(ResumeService.batch_reanalyze_resumes, ids)
    return {"code": 200, "message": f"已触发 {len(ids)} 份简历重测"}


@router.get("/")
async def list_resumes(
    status: str = Query(None, description="状态过滤：单个数字或逗号分隔，如 '2,3'"),
    name: str = Query(None),
    email: str = Query(None),
    phone: str = Query(None),
    university: str = Query(None),
    major: str = Query(None),
    skill: str = Query(None),
    schooltier: str = Query(None),
    degree: str = Query(None),
    date_from: str = Query(None, description="起始日期，支持 YYYY 或 YYYY-MM-DD"),
    date_to: str = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
):
    """
    多维度搜索简历

    优化点：
    1. 合并 status 和 status_list 为一个参数
    2. 去掉 Optional 类型注解（语法降级）
    3. 简化参数描述
    """
    try:
        return await ResumeService.get_resumes(
            status=status,
            name=name,
            email=email,
            phone=phone,
            university=university,
            major=major,
            skill=skill,
            schooltier=schooltier,
            degree=degree,
            date_from=date_from,
            date_to=date_to,
            page=page,
            page_size=page_size,
        )
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.delete("/")
async def delete_resume(
    name: str = Query(None),
    email: str = Query(None),
    phone: str = Query(None)
):
    """根据信息删除简历"""
    if not any([name, email, phone]):
        raise HTTPException(400, "请至少提供一个查询条件")

    count = await ResumeService.delete_resumes_by_info(name, email, phone)
    if count == 0:
        raise HTTPException(404, "未找到符合条件的简历")

    return {"message": f"成功删除 {count} 份简历"}