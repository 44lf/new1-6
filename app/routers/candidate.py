from fastapi import APIRouter, Depends, HTTPException

from fastapi import APIRouter, HTTPException, Body
from app.services.candidate_service import CandidateService

router = APIRouter(prefix="/candidates", tags=["Candidates"])

@router.get("/", summary="获取合格候选人列表")
async def list_candidates():
    return await CandidateService.get_all_candidates()

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