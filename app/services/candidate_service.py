from typing import Optional
from tortoise.expressions import Q, RawSQL
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
        获取候选人列表(过滤已删除)
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
            filters &= Q(prompt_id=prompt_id)

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

        # 3. 技能查询优化 - 先查询后过滤方案
        query = Candidate.filter(filters).prefetch_related("resume", "prompt")

        if skill_terms:
            # 获取所有符合前置条件的候选人
            all_candidates = await query.all()

            # Python层面过滤技能
            filtered_candidates = []
            for candidate in all_candidates:
                if not candidate.skills:
                    continue

                # 将候选人的技能列表转为小写
                candidate_skills_lower = [s.lower() if isinstance(s, str) else str(s).lower()
                                         for s in candidate.skills]

                # 检查是否所有搜索技能都在候选人技能中
                if all(term.lower() in candidate_skills_lower for term in skill_terms):
                    filtered_candidates.append(candidate)

            return filtered_candidates
        else:
            # 没有技能过滤,直接返回
            return await query.order_by("-created_at")

    @staticmethod
    async def update_candidate_info(candidate_id: int, update_data: dict):
        """更新候选人信息"""
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