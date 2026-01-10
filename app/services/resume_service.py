# app/services/resume_service.py - 优化版（代码量减少约 40%）
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
from app.enums.education import normalize_school_tier, infer_school_tier, expand_university_query
from tortoise.expressions import Q
from app.settings import MINIO_BUCKET_NAME


class ResumeService:
    _semaphore = asyncio.Semaphore(3)

    # ==================== 核心流程 ====================

    @staticmethod
    async def create_resume_record(file_url):
        return await Resume.create(file_url=file_url, status=0)

    @classmethod
    async def process_resume_workflow(cls, resume_id):
        """后台解析简历"""
        async with cls._semaphore:
            resume = await Resume.get_or_none(id=resume_id, is_deleted=0)
            if not resume:
                return

            # 手动录入跳过
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
        """执行解析并保存（合并多个内部方法）"""
        # 1. 获取提示词
        prompt = await PromptService.get_active_prompt()
        if not prompt:
            raise ValueError("未配置 Prompt")

        # 2. 下载文件
        file_bytes = await cls._download_pdf(resume.file_url)

        # 3. 解析 PDF
        text, avatar_data = PdfParser.parse_pdf(file_bytes)
        if not text or len(text.strip()) < 10:
            raise ValueError("PDF 内容为空")

        # 4. LLM 解析
        result = await LLMClient.parse_resume(text, prompt.content)

        # 5. 保存基本信息（简化字段映射）
        for k in ["name", "phone", "email", "university", "schooltier", "degree", "major"]:
            setattr(resume, k, result.get(k))

        resume.graduation_time = result.get("graduation_year")
        resume.skills = normalize_skills(result.get("skills", []))
        resume.work_experience = result.get("work_experience")
        resume.projects = result.get("projects")
        resume.parse_result = result
        resume.status = 2 if result.get("is_qualified") else 3
        await resume.save()

        # 6. 同步技能
        skills = await SkillService.get_or_create_skills(resume.skills or [])
        await resume.skill_tags.clear()
        if skills:
            await resume.skill_tags.add(*skills)

        # 7. 上传头像
        if avatar_data:
            import uuid
            ext = avatar_data["ext"]
            filename = f"avatars/{uuid.uuid4()}.{ext}"
            avatar_url = await MinioClient.upload_bytes(
                avatar_data["bytes"], filename, f"image/{ext}"
            )
            resume.avatar_url = avatar_url
            await resume.save()

        # 8. 保存评估
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
        """从 MinIO 下载文件"""
        if f"/{MINIO_BUCKET_NAME}/" in file_url:
            object_name = file_url.split(f"/{MINIO_BUCKET_NAME}/")[-1]
        else:
            object_name = file_url.split("/")[-1]

        file_bytes = await MinioClient.get_file_bytes(object_name)
        if not file_bytes:
            raise ValueError("文件下载失败")
        return file_bytes

    # ==================== 查询相关 ====================

    @staticmethod
    def _parse_date(value, is_end=False):
        """简化日期解析（去掉 Optional 类型）"""
        if not value:
            return None

        text = str(value).strip()
        if not text:
            return None

        # 处理纯年份
        if text.isdigit() and len(text) == 4:
            year = int(text)
            if is_end:
                return datetime(year, 12, 31, 23, 59, 59)
            return datetime(year, 1, 1, 0, 0, 0)

        # 处理日期（兼容 / 和 -）
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
        """解析状态参数（合并 status 和 status_list）"""
        if not status_str:
            return None

        # 去掉可能的中括号和空格
        clean = status_str.replace("[", "").replace("]", "").replace(" ", "")
        parts = clean.split(",")

        # 转换为整数列表
        result = []
        for p in parts:
            if p.isdigit():
                result.append(int(p))

        return result if result else None

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
        """多维度搜索（简化版）"""
        query = Resume.filter(is_deleted=0)
        schooltier_value = normalize_school_tier(schooltier)
        offset = (page - 1) * page_size

        # 状态过滤（统一处理）
        status_list = ResumeService._parse_status(status)
        if status_list:
            query = query.filter(status__in=status_list)

        # 文本字段（简化为循环）
        text_filters = {
            "name": name,
            "email": email,
            "phone": phone,
            "major": major,
        }
        for field, value in text_filters.items():
            if value:
                query = query.filter(**{f"{field}__icontains": value.strip()})

        # 学校（特殊处理）
        if university:
            terms = expand_university_query(university)
            if terms:
                q = Q(university__icontains=terms[0])
                for term in terms[1:]:
                    q |= Q(university__icontains=term)
                query = query.filter(q)

        # 学历
        if degree:
            deg_val = degree.value if hasattr(degree, "value") else str(degree)
            query = query.filter(degree__icontains=deg_val.strip())

        # 时间范围
        date_from_val = ResumeService._parse_date(date_from, False)
        date_to_val = ResumeService._parse_date(date_to, True)
        if date_from_val:
            query = query.filter(created_at__gte=date_from_val)
        if date_to_val:
            query = query.filter(created_at__lte=date_to_val)

        # 技能（多对多）
        use_distinct = False
        if skill:
            skill_terms = [s.strip().lower() for s in skill.replace("，", ",").split(",") if s.strip()]
            for term in skill_terms:
                query = query.filter(skill_tags__name=term)
            use_distinct = True

        # 学校层次（内存过滤 - 性能瓶颈点，后续优化）
        if schooltier_value:
            results_query = query.prefetch_related("skill_tags").order_by("-created_at")
            if use_distinct:
                results_query = results_query.distinct()
            results = await results_query
            results = [r for r in results if ResumeService._matches_tier(r, schooltier_value)]
            total = len(results)
            items = results[offset:offset + page_size]
        else:
            total = await query.count()
            results_query = query.prefetch_related("skill_tags").order_by("-created_at")
            if use_distinct:
                results_query = results_query.distinct()
            items = await results_query.offset(offset).limit(page_size)

        return {"items": items, "total": total, "page": page, "page_size": page_size}

    @staticmethod
    def _matches_tier(resume, target):
        """匹配学校层次"""
        tier = normalize_school_tier(resume.schooltier)
        if not tier or tier.value == "null":
            tier = infer_school_tier(resume.university)

        if target.value == "null":
            return tier is None
        return tier == target

    # ==================== 删除和批量 ====================

    @staticmethod
    async def delete_resumes_by_info(name=None, email=None, phone=None):
        """逻辑删除简历"""
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
        """批量重新解析"""
        tasks = [cls.process_resume_workflow(rid) for rid in resume_ids]
        if tasks:
            await asyncio.gather(*tasks)

    @staticmethod
    async def get_all_resume_ids():
        """获取所有ID"""
        return await Resume.filter(is_deleted=0).values_list("id", flat=True)