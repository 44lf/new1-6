import uuid
from typing import Optional
from tortoise.expressions import Q
from app.db.candidate_table import Candidate
from app.db.resume_table import Resume
from app.schemas.candidate import CandidateCreate
from app.services.prompt_service import PromptService
from app.services.resume_service import normalize_text_value, parse_skill_terms, normalize_skills_lower
import datetime

class CandidateService:
    @staticmethod
    async def create_candidate(payload: CandidateCreate) -> Optional[Candidate]:
        prompt_obj = None
        if payload.prompt_id:
            prompt_obj = await PromptService.get_prompt_by_id(payload.prompt_id)
            if not prompt_obj:
                return None

        resume = await Resume.create(
            file_url=f"manual://{uuid.uuid4()}",
            name=payload.name,
            phone=payload.phone,
            email=payload.email,
            university=payload.university,
            schooltier=payload.schooltier.value if payload.schooltier else None,
            degree=payload.degree.value if payload.degree else None,
            major=payload.major,
            graduation_time=payload.graduation_time,
            skills=normalize_skills_lower(payload.skills),
            is_qualified=True,
            status=2,
            prompt=prompt_obj,
        )

        candidate = await Candidate.create(
            file_url=resume.file_url,
            prompt=prompt_obj,
            name=payload.name,
            phone=payload.phone,
            email=payload.email,
            university=payload.university,
            schooltier=payload.schooltier.value if payload.schooltier else None,
            degree=payload.degree.value if payload.degree else None,
            major=payload.major,
            graduation_time=payload.graduation_time,
            skills=normalize_skills_lower(payload.skills),
            work_experience=payload.work_experience,
            project_experience=payload.project_experience,
            resume=resume,
            parse_result=None,
            is_deleted=0,
        )
        return candidate

    @staticmethod
    async def get_all_candidates(
        prompt_id: Optional[int] = None,
        name: Optional[str] = None,
        university: Optional[str] = None,
        schooltier: Optional[str] = None,
        degree: Optional[str] = None,
        major: Optional[str] = None,
        skill: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
    ):


        filters = Q(is_deleted=0)
        normalized_name = normalize_text_value(name)
        normalized_university = normalize_text_value(university)
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

        if normalized_major:
            filters &= Q(major__icontains=normalized_major)

        if schooltier:
            filters &= Q(schooltier=schooltier.value)

        if degree:
            filters &= Q(degree=degree.value)

        if date_from:
            filters &= Q(created_at__gte=date_from)

        if date_to:
            filters &= Q(created_at__lte=date_to)

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




