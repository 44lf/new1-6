from typing import Optional
from tortoise.expressions import Q
from app.db.candidate_table import Candidate
from app.services.resume_service import normalize_text_value, parse_skill_terms


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
        filters = Q(is_deleted=0)
        normalized_name = normalize_text_value(name)
        normalized_university = normalize_text_value(university)
        normalized_schooltier = normalize_text_value(schooltier)
        normalized_degree = normalize_text_value(degree)
        normalized_major = normalize_text_value(major)
        skill_terms = parse_skill_terms(skill)

        # 1. 岗位筛选
        if prompt_id:
            filters &= Q(resume__prompt_id=prompt_id)

        # 2. 真实维度的模糊搜索
        if normalized_name:
            filters &= Q(name__icontains=normalized_name)

        if normalized_university:
            filters &= Q(university__icontains=normalized_university)
        
        if normalized_schooltier:
            filters &= Q(schooltier__icontains=normalized_schooltier)
        
        if normalized_degree:
            filters &= Q(degree__icontains=normalized_degree)

        if normalized_major:
            filters &= Q(major__icontains=normalized_major)

        for term in skill_terms:
            filters &= Q(skills__contains=term)

        return await Candidate.filter(filters).prefetch_related("resume").order_by("-created_at")

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
