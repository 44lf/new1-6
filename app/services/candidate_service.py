from app.db.candidate_table import Candidate
from tortoise.expressions import Q
from typing import Optional

class CandidateService:
    @staticmethod
    async def get_all_candidates(
        prompt_id: Optional[int] = None,
        name: Optional[str] = None,
        university: Optional[str] = None,
        schooltier: Optional[str] = None,
        degree: Optional[str] = None,
        major: Optional[str] = None,
        skill: Optional[str] = None
    ):
        """
        获取候选人列表（支持高级筛选）
        """
        # 关联查询 resume
        query = Candidate.all().prefetch_related("resume")

        # 1. 岗位筛选
        if prompt_id:
            query = query.filter(resume__prompt_id=prompt_id)

        # 2. 真实维度的模糊搜索
        if name:
            # name__icontains 表示忽略大小写的模糊包含
            query = query.filter(name__icontains=name)

        if university:
            query = query.filter(university__icontains=university)
        
        if schooltier:
            query = query.filter(schooltier__icontains=schooltier)
        
        if degree:
            query = query.filter(degree__icontains=degree)

        if major:
            query = query.filter(major__icontains=major)

        # 3. 技能搜索
        # 由于 skills 是 JSONField (存储为 ["Vue", "Python"])，
        # 使用 icontains 可以匹配 JSON 字符串中的内容
        if skill:
            query = query.filter(skills__icontains=skill)

        return await query.order_by("-created_at")

    @staticmethod
    async def update_candidate_info(candidate_id: int, update_data: dict):
        candidate = await Candidate.get_or_none(id=candidate_id)
        if candidate:
            await candidate.update_from_dict(update_data)
            await candidate.save()
            return candidate
        return None

    @staticmethod
    async def delete_candidates_by_info(
        name: Optional[str] = None,
        email: Optional[str] = None,
        phone: Optional[str] = None
    ) -> int:
        """
        更加真实的删除功能：根据姓名、邮箱或电话删除
        返回删除的记录数
        """
        # 安全检查：防止未传参数导致误删全表
        if not any([name, email, phone]):
            return 0

        query = Candidate.all()

        # 删除操作建议稍微严格一点，防止手滑
        # 但为了符合"真实操作"，这里支持通过姓名删除
        # 如果提供了多个条件，是 AND 关系（必须同时满足）
        if name:
            query = query.filter(name=name)
        if email:
            query = query.filter(email=email)
        if phone:
            query = query.filter(phone=phone)

        count = await query.count()
        if count > 0:
            await query.delete()

        return count