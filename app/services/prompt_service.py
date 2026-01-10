from app.db.prompt_table import Prompt
from tortoise.transactions import in_transaction
from typing import List, Optional

class PromptService:
    @staticmethod
    async def get_active_prompt() -> Optional[Prompt]:
        """获取当前启用的提示词 (必须未被删除)"""
        return await Prompt.get_or_none(is_active=True, is_deleted=0)

    @staticmethod
    async def activate_prompt(prompt_id: int) -> bool:
        """
        启用指定提示词
        """
        async with in_transaction():
            # 1. 只有未删除的才能被启用
            prompt = await Prompt.get_or_none(id=prompt_id, is_deleted=0)
            if not prompt:
                return False

            # 2. 把所有提示词设为 False (这里不需要过滤 is_deleted，全停即可，比较安全)
            await Prompt.all().update(is_active=False)
            
            # 3. 启用目标
            prompt.is_active = True
            await prompt.save()
            return True

    @staticmethod
    async def create_prompt(name: str, content: str, is_active: bool = False) -> Prompt:
        """创建新提示词"""
        async with in_transaction():
            if is_active:
                await Prompt.all().update(is_active=False)
            # 默认 is_deleted=0
            return await Prompt.create(name=name, content=content, is_active=is_active)
    
    @staticmethod
    async def get_prompt_by_id(prompt_id: int) -> Optional[Prompt]:
        """根据ID获取提示词"""
        return await Prompt.get_or_none(id=prompt_id, is_deleted=0)
    
    @staticmethod
    async def get_all_prompts(offset: int = 0, limit: int = 20) -> List[Prompt]:
        """获取所有提示词 (未删除的)，支持分页"""
        return await Prompt.filter(is_deleted=0).offset(offset).limit(limit).all()
    
    @staticmethod
    async def update_prompt(prompt_id: int, name: Optional[str] = None, 
                          content: Optional[str] = None) -> Optional[Prompt]:
        """更新提示词内容"""
        prompt = await Prompt.get_or_none(id=prompt_id, is_deleted=0)
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
        """逻辑删除提示词"""
        prompt = await Prompt.get_or_none(id=prompt_id, is_deleted=0)
        if not prompt:
            return False
        
        # 逻辑删除：标记为 1，并自动禁用
        prompt.is_deleted = 1
        prompt.is_active = False 
        await prompt.save()
        return True
    
    @staticmethod
    async def deactivate_all() -> None:
        """禁用所有提示词"""
        await Prompt.all().update(is_active=False)
