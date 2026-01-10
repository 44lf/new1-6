# app/services/resume_service.py - 修复学校层次查询 Bug
import asyncio
from datetime import datetime
from app.db.resume_table import Resume
from app.db.resume_evaluation_table import ResumeEvaluation
from app.services.prompt_service import PromptService
from app.services.skill_service import SkillService
from app.utils.minio_client import MinioClient
from app.utils.llm_client import LLMClient
from app.utils.pdf_parser import PdfParser
from app.utils.helpers import normalize_skills
from app.enums.education import (
    normalize_school_tier,
    infer_school_tier,
    expand_university_query,
    SCHOOL_TIER_985,
    SCHOOL_TIER_211,
    SCHOOL_TIER_DOUBLE_FIRST,
)
from tortoise.expressions import Q
from app.settings import MINIO_BUCKET_NAME


class ResumeService:
    _semaphore = asyncio.Semaphore(3)

    # ==================== 核心流程（保持不变）====================

    @staticmethod
    async def create_resume_record(file_url):
        return await Resume.create(file_url=file_url, status=0)

    @staticmethod
    async def create_manual_resume(**payload):
        skills = normalize_skills(payload.get("skills"))
        return await Resume.create(
            file_url=payload["file_url"],
            status=2,
            name=payload.get("name"),
            phone=payload.get("phone"),
            email=payload.get("email"),
            university=payload.get("university"),
            schooltier=payload.get("schooltier"),
            degree=payload.get("degree"),
            major=payload.get("major"),
            graduation_time=payload.get("graduation_time"),
            skills=skills or None,
            work_experience=payload.get("work_experience"),
            projects=payload.get("projects"),
        )

    @classmethod
    async def process_resume_workflow(cls, resume_id):
        async with cls._semaphore:
            resume = await Resume.get_or_none(id=resume_id, is_deleted=0)
            if not resume:
                return

            if resume.file_url.startswith("manual://"):
                if resume.status != 2:
                    resume.status = 2
                    await resume.save()
                return

            resume.status = 1
            await resume.save()

            try:
                await cls._parse_and_save(resume)
            except Exception as e:
                print(f"简历 {resume_id} 解析失败: {e}")
                resume.status = 4
                await resume.save()

    @classmethod
    async def _parse_and_save(cls, resume):
        prompt = await PromptService.get_active_prompt()
        if not prompt:
            raise ValueError("未配置 Prompt")

        file_bytes = await cls._download_pdf(resume.file_url)
        text, avatar_data = PdfParser.parse_pdf(file_bytes)
        if not text or len(text.strip()) < 10:
            raise ValueError("PDF 内容为空")

        result = await LLMClient.parse_resume(text, prompt.content)

        for k in ["name", "phone", "email", "university", "schooltier", "degree", "major"]:
            setattr(resume, k, result.get(k))

        resume.graduation_time = result.get("graduation_year")
        resume.skills = normalize_skills(result.get("skills", []))
        resume.work_experience = result.get("work_experience")
        resume.projects = result.get("projects")
        resume.parse_result = result
        resume.status = 2 if result.get("is_qualified") else 3
        await resume.save()

        skills = await SkillService.get_or_create_skills(resume.skills or [])
        await resume.skill_tags.clear()
        if skills:
            await resume.skill_tags.add(*skills)

        if avatar_data:
            import uuid
            ext = avatar_data["ext"]
            filename = f"avatars/{uuid.uuid4()}.{ext}"
            avatar_url = await MinioClient.upload_bytes(
                avatar_data["bytes"], filename, f"image/{ext}"
            )
            resume.avatar_url = avatar_url
            await resume.save()

        await ResumeEvaluation.update_or_create(
            defaults={
                "score": result.get("score"),
                "is_qualified": result.get("is_qualified", False),
                "reason": result.get("reason"),
                "evaluated_at": datetime.utcnow(),
            },
            resume=resume,
            prompt=prompt,
        )

    @staticmethod
    async def _download_pdf(file_url):
        if f"/{MINIO_BUCKET_NAME}/" in file_url:
            object_name = file_url.split(f"/{MINIO_BUCKET_NAME}/")[-1]
        else:
            object_name = file_url.split("/")[-1]

        file_bytes = await MinioClient.get_file_bytes(object_name)
        if not file_bytes:
            raise ValueError("文件下载失败")
        return file_bytes

    # ==================== 修复的查询方法 ====================

    @staticmethod
    def _parse_date(value, is_end=False):
        if not value:
            return None

        text = str(value).strip()
        if not text:
            return None

        if text.isdigit() and len(text) == 4:
            year = int(text)
            if is_end:
                return datetime(year, 12, 31, 23, 59, 59)
            return datetime(year, 1, 1, 0, 0, 0)

        text = text.replace("/", "-")
        try:
            parsed = datetime.fromisoformat(text)
            if is_end:
                return parsed.replace(hour=23, minute=59, second=59)
            return parsed
        except:
            raise ValueError("日期格式错误，请使用 YYYY 或 YYYY-MM-DD")

    @staticmethod
    def _parse_status(status_str):
        if not status_str:
            return None

        clean = status_str.replace("[", "").replace("]", "").replace(" ", "")
        parts = clean.split(",")
        result = []
        for p in parts:
            if p.isdigit():
                result.append(int(p))

        return result if result else None

    @staticmethod
    def _build_school_tier_filter(schooltier_value):
        """
        【修复 Bug 3】
        构建学校层次的数据库查询条件，避免内存过滤
        """
        if not schooltier_value:
            return None

        tier_name = schooltier_value.value

        # 构建 Q 查询条件
        q = Q(schooltier__icontains=tier_name)

        # 如果是具体层次，添加对应学校名单
        if tier_name == "985":
            for school in SCHOOL_TIER_985:
                q |= Q(university__icontains=school)
        elif tier_name == "211":
            for school in SCHOOL_TIER_211:
                q |= Q(university__icontains=school)
        elif tier_name == "双一流":
            for school in SCHOOL_TIER_DOUBLE_FIRST:
                q |= Q(university__icontains=school)

        return q

    @staticmethod
    async def get_resumes(
        status=None,
        name=None,
        email=None,
        phone=None,
        university=None,
        schooltier=None,
        degree=None,
        major=None,
        skill=None,
        date_from=None,
        date_to=None,
        page=1,
        page_size=20,
    ):
        """【修复 Bug 3】多维度搜索 - 使用数据库过滤"""
        query = Resume.filter(is_deleted=0)
        offset = (page - 1) * page_size
        use_distinct = False

        # 状态过滤
        status_list = ResumeService._parse_status(status)
        if status_list:
            query = query.filter(status__in=status_list)

        # 文本字段过滤
        text_filters = {
            "name": name,
            "email": email,
            "phone": phone,
            "major": major,
        }
        for field, value in text_filters.items():
            if value:
                query = query.filter(**{f"{field}__icontains": value.strip()})

        # 学校过滤
        if university:
            terms = expand_university_query(university)
            if terms:
                q = Q(university__icontains=terms[0])
                for term in terms[1:]:
                    q |= Q(university__icontains=term)
                query = query.filter(q)

        # 学历过滤
        if degree:
            deg_val = degree.value if hasattr(degree, "value") else str(degree)
            query = query.filter(degree__icontains=deg_val.strip())

        # 时间范围过滤
        date_from_val = ResumeService._parse_date(date_from, False)
        date_to_val = ResumeService._parse_date(date_to, True)
        if date_from_val:
            query = query.filter(created_at__gte=date_from_val)
        if date_to_val:
            query = query.filter(created_at__lte=date_to_val)

        # 【修复 Bug 7】技能过滤（多对多） - 统一小写
        if skill:
            skill_terms = [s.strip().lower() for s in skill.replace("，", ",").split(",") if s.strip()]
            for term in skill_terms:
                # 技能在数据库中是小写存储的，直接用 = 即可
                query = query.filter(skill_tags__name=term)
            use_distinct = True

        # 【修复】学校层次过滤 - 使用数据库查询
        schooltier_value = normalize_school_tier(schooltier)
        if schooltier_value:
            tier_q = ResumeService._build_school_tier_filter(schooltier_value)
            if tier_q:
                query = query.filter(tier_q)

        # 执行查询
        total = await query.count()
        results_query = query.prefetch_related("skill_tags").order_by("-created_at")
        if use_distinct:
            results_query = results_query.distinct()
        items = await results_query.offset(offset).limit(page_size)

        return {"items": items, "total": total, "page": page, "page_size": page_size}

    # ==================== 删除和批量（保持不变）====================

    @staticmethod
    async def delete_resumes_by_info(name=None, email=None, phone=None):
        if not any([name, email, phone]):
            return 0

        query = Resume.filter(is_deleted=0)
        if name:
            query = query.filter(name=name)
        if email:
            query = query.filter(email=email)
        if phone:
            query = query.filter(phone=phone)

        ids = await query.values_list("id", flat=True)
        count = len(ids)

        if count > 0:
            await Resume.filter(id__in=ids).update(is_deleted=1)
            await ResumeEvaluation.filter(resume_id__in=ids).delete()

        return count

    @classmethod
    async def batch_reanalyze_resumes(cls, resume_ids):
        """【修复 Bug 4】批量重新解析 - 分批处理避免死锁"""
        batch_size = 10  # 每批处理10个
        for i in range(0, len(resume_ids), batch_size):
            batch = resume_ids[i:i + batch_size]
            tasks = [cls.process_resume_workflow(rid) for rid in batch]
            await asyncio.gather(*tasks, return_exceptions=True)
            # 每批之间稍微延迟，避免数据库压力
            if i + batch_size < len(resume_ids):
                await asyncio.sleep(0.5)

    @staticmethod
    async def get_all_resume_ids():
        return await Resume.filter(is_deleted=0).values_list("id", flat=True)