from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel
from app.services.prompt_service import PromptService

router = APIRouter(prefix="/prompts", tags=["Prompts"])

# 定义一个简单的请求体模型
class PromptCreate(BaseModel):
    name: str
    content: str

@router.post("/", summary="创建新提示词")
async def create_prompt(prompt: PromptCreate):
    return await PromptService.create_prompt(prompt.name, prompt.content)

@router.get("/", summary="获取所有提示词")
async def get_all_prompts():
    return await PromptService.get_all_prompts()

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