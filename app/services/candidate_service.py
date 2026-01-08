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
        获取候选人列表（过滤已删除）
        """
        # 只查未删除的
        query = Candidate.filter(is_deleted=0).prefetch_related("resume")

        # 1. 岗位筛选
        if prompt_id:
            query = query.filter(resume__prompt_id=prompt_id)

        # 2. 真实维度的模糊搜索
        if name:
            query = query.filter(name__icontains=name)

        if university:
            query = query.filter(university__icontains=university)
        
        if schooltier:
            query = query.filter(schooltier__icontains=schooltier)
        
        if degree:
            query = query.filter(degree__icontains=degree)

        if major:
            query = query.filter(major__icontains=major)

        if skill:
            query = query.filter(skills__icontains=skill)

        return await query.order_by("-created_at")

    @staticmethod
    async def update_candidate_info(candidate_id: int, update_data: dict):
        # 只能更新未删除的
        candidate = await Candidate.get_or_none(id=candidate_id, is_deleted=0)
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
        逻辑删除候选人
        """
        if not any([name, email, phone]):
            return 0

        # 查询未删除的
        query = Candidate.filter(is_deleted=0)

        if name:
            query = query.filter(name=name)
        if email:
            query = query.filter(email=email)
        if phone:
            query = query.filter(phone=phone)

        count = await query.count()
        if count > 0:
            # 逻辑删除
            await query.update(is_deleted=1)

        return count