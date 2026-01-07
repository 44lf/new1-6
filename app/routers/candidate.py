from fastapi import APIRouter, HTTPException, Body, Query
from typing import Optional
from app.services.candidate_service import CandidateService
router = APIRouter(prefix="/candidates", tags=["Candidates"])

@router.get("/", summary="获取合格候选人列表")
async def list_candidates(
    prompt_id: Optional[int] = Query(None, description="按岗位(提示词ID)筛选")
):
    """
    查询候选人列表。
    如果不传 prompt_id，返回所有；
    如果传了，只返回该特定岗位的候选人。
    """
    return await CandidateService.get_all_candidates(prompt_id)

@router.put("/{candidate_id}", summary="更新候选人信息")
async def update_candidate(candidate_id: int, payload: dict = Body(...)):
    """
    人工修正候选人信息
    payload 示例: {"name": "修正后的名字", "phone": "138..."}
    """
    updated_obj = await CandidateService.update_candidate_info(candidate_id, payload)
    if not updated_obj:
        raise HTTPException(status_code=404, detail="候选人不存在")
    return updated_obj