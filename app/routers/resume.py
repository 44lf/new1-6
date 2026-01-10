# app/routers/resume.py - 优化版（代码量减少约 30%）
import uuid
from fastapi import APIRouter, UploadFile, File, BackgroundTasks, HTTPException, Query, Form
from app.services.resume_service import ResumeService
from app.utils.minio_client import MinioClient
from app.db.resume_table import Resume
from app.enums.education import SchoolTier, Degree

router = APIRouter(prefix="/resumes", tags=["Resumes"])


@router.post("/upload", summary="上传简历（PDF）")
async def upload_resume(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="PDF 格式简历文件"),
):
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


@router.post(
    "/manual",
    summary="手动录入简历",
    description="通过表单字段手动录入简历信息（姓名和手机号必填）。",
)
async def create_manual_resume(
    name: str = Form(..., description="姓名"),
    phone: str = Form(..., description="手机号"),
    email: str = Form(None, description="邮箱"),
    university: str = Form(None, description="学校"),
    schooltier: SchoolTier = Form(None, description="学校层次"),
    degree: Degree = Form(None, description="学历"),
    major: str = Form(None, description="专业"),
    graduation_time: str = Form(None, description="毕业时间（字符串）"),
    skills: str = Form(None, description="技能（逗号分隔）"),
    work_experience: str = Form(None, description="工作经历"),
    projects: str = Form(None, description="项目经历"),
):
    def _clean_text(value):
        if value is None:
            return None
        text = str(value).strip()
        return text or None

    name_value = _clean_text(name)
    phone_value = _clean_text(phone)
    if not name_value or not phone_value:
        raise HTTPException(400, "姓名和手机号不能为空")
    manual_url = f"manual://{uuid.uuid4()}"
    def _enum_value(value):
        if not value:
            return None
        enum_value = value.value if hasattr(value, "value") else str(value)
        return None if enum_value == "null" else enum_value

    resume = await ResumeService.create_manual_resume(
        file_url=manual_url,
        name=name_value,
        phone=phone_value,
        email=_clean_text(email),
        university=_clean_text(university),
        schooltier=_enum_value(schooltier),
        degree=_enum_value(degree),
        major=_clean_text(major),
        graduation_time=_clean_text(graduation_time),
        skills=_clean_text(skills),
        work_experience=_clean_text(work_experience),
        projects=_clean_text(projects),
    )
    return {"code": 200, "message": "手动录入成功", "data": {"resume_id": resume.id}}


@router.post("/{resume_id}/analyze", summary="重新分析单份简历")
async def reanalyze_one(resume_id: int, background_tasks: BackgroundTasks):
    """重新分析单份简历"""
    resume = await Resume.get_or_none(id=resume_id)
    if not resume:
        raise HTTPException(404, "简历不存在")

    background_tasks.add_task(ResumeService.process_resume_workflow, resume.id)
    return {"code": 200, "message": "已重新加入解析队列"}


@router.post("/reanalyze/all", summary="批量重新分析所有简历")
async def reanalyze_all(background_tasks: BackgroundTasks):
    """批量重新筛选所有简历"""
    ids = await ResumeService.get_all_resume_ids()
    if not ids:
        return {"code": 200, "message": "简历库为空"}

    background_tasks.add_task(ResumeService.batch_reanalyze_resumes, ids)
    return {"code": 200, "message": f"已触发 {len(ids)} 份简历重测"}


@router.get("/", summary="多维度搜索简历")
async def list_resumes(
    status: str = Query(None, description="状态过滤：单个数字或逗号分隔，如 '2,3'"),
    name: str = Query(None, description="姓名（支持模糊匹配）"),
    email: str = Query(None, description="邮箱"),
    phone: str = Query(None, description="手机号"),
    university: str = Query(None, description="学校名称（支持别名）"),
    major: str = Query(None, description="专业"),
    skill: str = Query(None, description="技能关键字"),
    schooltier: SchoolTier = Query(None, description="学校层次"),
    degree: Degree = Query(None, description="学历"),
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


@router.delete("/", summary="根据信息删除简历")
async def delete_resume(
    name: str = Query(None, description="姓名"),
    email: str = Query(None, description="邮箱"),
    phone: str = Query(None, description="手机号"),
):
    """根据信息删除简历"""
    if not any([name, email, phone]):
        raise HTTPException(400, "请至少提供一个查询条件")

    count = await ResumeService.delete_resumes_by_info(name, email, phone)
    if count == 0:
        raise HTTPException(404, "未找到符合条件的简历")

    return {"message": f"成功删除 {count} 份简历"}
