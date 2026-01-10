import uuid
from datetime import datetime
from fastapi import APIRouter, UploadFile, File, BackgroundTasks, HTTPException, Query
from typing import Optional

from app.services.resume_service import ResumeService
from app.utils.minio_client import MinioClient
from app.db.resume_table import Resume
from app.enums.education import SchoolTier, Degree


router = APIRouter(prefix="/resumes", tags=["Resumes"])

@router.post("/upload", summary="上传简历PDF")
async def upload_resume(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
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






@router.post("/{resume_id}/analyze", summary="重新分析单份简历")
async def resume_analyze(
    resume_id: int,
    background_tasks: BackgroundTasks,
):
    resume = await Resume.get_or_none(id=resume_id)
    if not resume:
        raise HTTPException(status_code=404, detail="简历不存在")

    background_tasks.add_task(
        ResumeService.process_resume_workflow,
        resume.id
    )

    return {"code": 200, "message": "已将简历重新加入解析队列"}

@router.post("/reanalyze/all", summary="一键重新筛选所有简历")
async def reanalyze_all_resumes(
    background_tasks: BackgroundTasks,
):
    """
    **全量重新筛选**：
    当更换了 Prompt 后，点击此按钮。
    后台会用最新的提示词对库里所有简历重新进行 AI 评估。
    """
    all_ids = await ResumeService.get_all_resume_ids()

    if not all_ids:
        return {"code": 200, "message": "当前简历库为空，无需重测"}

    background_tasks.add_task(ResumeService.batch_reanalyze_resumes, all_ids)

    return {
        "code": 200,
        "message": f"已触发全量重测任务，共 {len(all_ids)} 份简历正在后台重新排队解析...",
    }

@router.get("/", summary="多维度搜索简历")
async def list_resumes(
    status: Optional[int] = Query(None, description="状态(0=未处理, 1=处理中, 2=合格, 3=不合格, 4=失败)"),
    status_list: Optional[str] = Query(
        None,
        description="状态列表，支持如 1,2 或 [状态1，状态2] 格式",
    ),
    name: Optional[str] = Query(None, description="搜索姓名"),
    email: Optional[str] = Query(None, description="搜索邮箱"),
    phone: Optional[str] = Query(None, description="搜索电话"),
    university: Optional[str] = Query(None, description="搜索学校"),
    major: Optional[str] = Query(None, description="搜索专业"),
    skill: Optional[str] = Query(None, description="搜索技能 (如: Python)"),
    schooltier: Optional[SchoolTier] = Query(None, description="学校层次"),
    degree: Optional[Degree] = Query(None, description='学历层次'),
    date_from: Optional[str] = Query(None, description="起始日期/时间 (>=)，支持 YYYY 或 YYYY-MM-DD"),
    date_to: Optional[str] = Query(None, description="结束日期/时间 (<=)，支持 YYYY 或 YYYY-MM-DD"),
    page: int = Query(1, ge=1, description="页码，从1开始"),
    page_size: int = Query(20, ge=1, le=200, description="每页数量"),
    filter1_field: Optional[str] = Query(None, description="筛选1字段(如 name/university/degree/major/email/phone/schooltier/skill)"),
    filter1_op: Optional[str] = Query(None, description="筛选1关系(contains/not_contains)"),
    filter1_value: Optional[str] = Query(None, description="筛选1内容"),
    logic1: Optional[str] = Query(None, description="筛选1与筛选2的逻辑(and/or/not)"),
    filter2_field: Optional[str] = Query(None, description="筛选2字段(如 name/university/degree/major/email/phone/schooltier/skill)"),
    filter2_op: Optional[str] = Query(None, description="筛选2关系(contains/not_contains)"),
    filter2_value: Optional[str] = Query(None, description="筛选2内容"),
    logic2: Optional[str] = Query(None, description="筛选2与筛选3的逻辑(and/or/not)"),
    filter3_field: Optional[str] = Query(None, description="筛选3字段(如 name/university/degree/major/email/phone/schooltier/skill)"),
    filter3_op: Optional[str] = Query(None, description="筛选3关系(contains/not_contains)"),
    filter3_value: Optional[str] = Query(None, description="筛选3内容"),
    logic3: Optional[str] = Query(None, description="筛选3与筛选4的逻辑(and/or/not)"),
    filter4_field: Optional[str] = Query(None, description="筛选4字段(如 name/university/degree/major/email/phone/schooltier/skill)"),
    filter4_op: Optional[str] = Query(None, description="筛选4关系(contains/not_contains)"),
    filter4_value: Optional[str] = Query(None, description="筛选4内容"),
):
    try:
        return await ResumeService.get_resumes(
            status=status,
            status_list=status_list,
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
            filter1_field=filter1_field,
            filter1_op=filter1_op,
            filter1_value=filter1_value,
            logic1=logic1,
            filter2_field=filter2_field,
            filter2_op=filter2_op,
            filter2_value=filter2_value,
            logic2=logic2,
            filter3_field=filter3_field,
            filter3_op=filter3_op,
            filter3_value=filter3_value,
            logic3=logic3,
            filter4_field=filter4_field,
            filter4_op=filter4_op,
            filter4_value=filter4_value,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

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
