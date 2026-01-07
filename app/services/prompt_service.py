from app.db.prompt_table import Prompt
from tortoise.transactions import in_transaction
from typing import List, Optional

class PromptService:
    @staticmethod
    async def get_active_prompt() -> Optional[Prompt]:
        """获取当前启用的提示词"""
        return await Prompt.get_or_none(is_active=True)

    @staticmethod
    async def activate_prompt(prompt_id: int) -> bool:
        """
        启用指定提示词，并自动禁用其他所有提示词（互斥逻辑）
        使用事务确保数据一致性
        """
        async with in_transaction():
            # 1. 把所有提示词设为 False
            await Prompt.all().update(is_active=False)
            
            # 2. 把指定的设为 True
            prompt = await Prompt.get_or_none(id=prompt_id)
            if prompt:
                prompt.is_active = True
                await prompt.save()
                return True
            return False

    @staticmethod
    async def create_prompt(name: str, content: str, is_active: bool = False) -> Prompt:
        """创建新提示词"""
        async with in_transaction():
            # 如果新提示词要设为启用，先禁用所有其他提示词
            if is_active:
                await Prompt.all().update(is_active=False)
            return await Prompt.create(name=name, content=content, is_active=is_active)
    
    @staticmethod
    async def get_prompt_by_id(prompt_id: int) -> Optional[Prompt]:
        """根据ID获取提示词"""
        return await Prompt.get_or_none(id=prompt_id)
    
    @staticmethod
    async def get_all_prompts() -> List[Prompt]:
        """获取所有提示词"""
        return await Prompt.all()
    
    @staticmethod
    async def update_prompt(prompt_id: int, name: Optional[str] = None, 
                          content: Optional[str] = None) -> Optional[Prompt]:
        """更新提示词内容"""
        prompt = await Prompt.get_or_none(id=prompt_id)
        if not prompt:
            return None
        
        if name is not None:
            prompt.name = name
        if content is not None:
            prompt.content = content
        
        await prompt.save()
        return prompt
    
    @staticmethod
    async def delete_prompt(prompt_id: int) -> bool:
        """删除提示词"""
        prompt = await Prompt.get_or_none(id=prompt_id)
        if not prompt:
            return False
        
        # 如果删除的是当前启用的提示词，可能需要特殊处理
        # 这里简单删除，具体逻辑根据业务需求调整
        await prompt.delete()
        return True
    
    @staticmethod
    async def deactivate_all() -> None:
        """禁用所有提示词"""
        await Prompt.all().update(is_active=False)
    
    @staticmethod
    async def search_prompts(keyword: str) -> List[Prompt]:
        """根据关键词搜索提示词（名称或内容）"""
        return await Prompt.filter(name__icontains=keyword) | await Prompt.filter(content__icontains=keyword)
    
    @staticmethod
    async def get_prompts_count() -> int:
        """获取提示词总数"""
        return await Prompt.all().count()