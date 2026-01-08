from fastapi import APIRouter, HTTPException, Body, Query
from pydantic import BaseModel
from typing import Optional
from app.services.prompt_service import PromptService

router = APIRouter(prefix="/prompts", tags=["Prompts"])

# 定义一个简单的请求体模型
class PromptCreate(BaseModel):
    name: str
    content: str

class PromptUpdate(BaseModel):
    name: Optional[str] = None
    content: Optional[str] = None

@router.post("/", summary="创建新提示词")
async def create_prompt(prompt: PromptCreate):
    return await PromptService.create_prompt(prompt.name, prompt.content)

@router.get("/", summary="获取所有提示词")
async def get_all_prompts(
    page: int = Query(1, ge=1, description="页码，从1开始"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量")
):
    offset = (page - 1) * page_size
    return await PromptService.get_all_prompts(offset=offset, limit=page_size)

@router.put("/{prompt_id}", summary="更新提示词")
async def update_prompt(prompt_id: int, payload: PromptUpdate = Body(...)):
    updated = await PromptService.update_prompt(
        prompt_id,
        name=payload.name,
        content=payload.content
    )
    if not updated:
        raise HTTPException(status_code=404, detail="提示词不存在")
    return updated

@router.put("/{prompt_id}/active", summary="启用指定提示词")
async def activate_prompt(prompt_id: int):
    """
    启用某个提示词，这会自动禁用其他所有提示词
    """
    success = await PromptService.activate_prompt(prompt_id)
    if not success:
        raise HTTPException(status_code=404, detail="提示词不存在")
    return {"message": "启用成功"}

@router.delete("/{prompt_id}", summary="删除提示词")
async def delete_prompt(prompt_id: int):
    success = await PromptService.delete_prompt(prompt_id)
    if not success:
        raise HTTPException(status_code=404, detail="删除失败，ID不存在")
    return {"message": "删除成功"}
