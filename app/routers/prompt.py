# app/routers/prompt.py - 优化版（代码量减少约 25%）
from fastapi import APIRouter, HTTPException, Body, Query
from pydantic import BaseModel, Field
from app.services.prompt_service import PromptService

router = APIRouter(prefix="/prompts", tags=["Prompts"])


# 请求体模型（合并 Create 和 Update）
class PromptData(BaseModel):
    name: str = Field(None, description="提示词名称")
    content: str = Field(None, description="提示词内容")


@router.post("/", summary="创建提示词")
async def create_prompt(data: PromptData):
    """创建提示词"""
    if not data.name or not data.content:
        raise HTTPException(400, "name 和 content 不能为空")
    return await PromptService.create_prompt(data.name, data.content)


@router.get("/", summary="获取提示词列表")
async def list_prompts(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
):
    """获取所有提示词"""
    offset = (page - 1) * page_size
    return await PromptService.get_all_prompts(offset, page_size)


@router.put("/{prompt_id}", summary="更新提示词")
async def update_prompt(prompt_id: int, data: PromptData = Body(...)):
    """更新提示词"""
    updated = await PromptService.update_prompt(prompt_id, data.name, data.content)
    if not updated:
        raise HTTPException(404, "提示词不存在")
    return updated


@router.put("/{prompt_id}/active", summary="启用提示词")
async def activate_prompt(prompt_id: int):
    """启用提示词"""
    if not await PromptService.activate_prompt(prompt_id):
        raise HTTPException(404, "提示词不存在")
    return {"message": "启用成功"}


@router.delete("/{prompt_id}", summary="删除提示词")
async def delete_prompt(prompt_id: int):
    """删除提示词"""
    if not await PromptService.delete_prompt(prompt_id):
        raise HTTPException(404, "删除失败")
    return {"message": "删除成功"}
