from fastapi import APIRouter, HTTPException, Body, Query, Form
from typing import Optional
from app.schemas.candidate import CandidateCreate
from app.services.candidate_service import CandidateService
from app.enums.education import SchoolTier, Degree

router = APIRouter(prefix="/candidates", tags=["Candidates"])

@router.post("/", summary="手动新增候选人")
async def create_candidate(payload: CandidateCreate = Body(...)):
    candidate = await CandidateService.create_candidate(payload)
    if not candidate:
        raise HTTPException(status_code=404, detail="关联岗位不存在")
    return candidate

@router.get("/", summary="多维度搜索候选人")
async def list_candidates(
    prompt_id: Optional[int] = Query(None, description="按岗位(提示词ID)筛选"),
    name: Optional[str] = Query(None, description="搜索姓名 (支持模糊)"),
    university: Optional[str] = Query(None, description="搜索毕业院校 (支持模糊)"),
    major: Optional[str] = Query(None, description="搜索专业 (支持模糊)"),
    skill: Optional[str] = Query(None, description="搜索技能 (如: Python)"),
    schooltier: Optional[SchoolTier] = Query(None, description="学校层次"),
    degree: Optional[Degree] = Query(None, description='学历层次'),
    date_from: Optional[datetime] = Query(None, description="起始日期/时间 (>=)"),
    date_to: Optional[datetime] = Query(None, description="结束日期/时间 (<=)"),
):
    """
    **升级版查询功能**：
    不再局限于岗位，现在你可以像 HR 一样搜索：
    - "找一个会 Python 的" (`skill=Python`)
    - "找清华毕业的" (`university=清华`)
    - "找叫张三的" (`name=张三`)
    """
    return await CandidateService.get_all_candidates(
        prompt_id=prompt_id,
        name=name,
        university=university,
        major=major,
        skill=skill,
        schooltier=schooltier,
        degree=degree,
        date_from=date_from,
        date_to=date_to,
    )

@router.put("/{candidate_id}", summary="更新候选人信息")
async def update_candidate(candidate_id: int, payload: dict = Body(...)):
    """
    人工修正候选人信息
    """
    updated_obj = await CandidateService.update_candidate_info(candidate_id, payload)
    if not updated_obj:
        raise HTTPException(status_code=404, detail="候选人不存在")
    return updated_obj

@router.delete("/", summary="根据信息删除候选人")
async def delete_candidate_by_info(
    name: Optional[str] = Query(None, description="按姓名删除"),
    email: Optional[str] = Query(None, description="按邮箱删除"),
    phone: Optional[str] = Query(None, description="按电话删除")
):
    """
    **更真实的删除功能**：
    不需要知道 ID，直接告诉系统："把那个叫张三的删掉"。
    注意：如果只传姓名，可能会删除重名的人，建议配合邮箱或电话使用。
    """
    if not any([name, email, phone]):
        raise HTTPException(status_code=400, detail="请至少提供姓名、邮箱或电话中的一项")

    deleted_count = await CandidateService.delete_candidates_by_info(name, email, phone)

    if deleted_count == 0:
        raise HTTPException(status_code=404, detail="未找到符合条件的候选人")

    return {"message": f"成功删除了 {deleted_count} 名候选人"}
