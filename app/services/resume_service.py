# app/services/resume_service.py
"""
简历服务 - 简化版
"""
import asyncio
from datetime import datetime
from typing import Optional, List

from app.db.resume_table import Resume
from app.db.resume_evaluation_table import ResumeEvaluation
from app.services.prompt_service import PromptService
from app.services.skill_service import SkillService
from app.utils.minio_client import MinioClient
from app.utils.llm_client import LLMClient
from app.utils.pdf_parser import PdfParser
from app.utils.helpers import normalize_skills
from app.settings import MINIO_BUCKET_NAME


class ResumeService:
    """简历处理服务"""

    # 并发控制: 同时最多处理3份简历
    _semaphore = asyncio.Semaphore(3)

    # ==================== 核心业务流程 ====================

    @staticmethod
    async def create_resume_record(file_url: str) -> Resume:
        """创建简历记录"""
        return await Resume.create(file_url=file_url, status=0)

    @classmethod
    async def process_resume_workflow(cls, resume_id: int):
        """
        【核心流程】后台异步解析简历

        流程:
        1. 获取简历记录
        2. 下载 PDF 文件
        3. 解析 PDF (提取文本和头像)
        4. 调用 LLM 解析
        5. 保存结果
        6. 上传头像
        7. 保存评估记录
        """
        async with cls._semaphore:
            # 1. 获取简历
            resume = await Resume.get_or_none(id=resume_id, is_deleted=0)
            if not resume:
                return

            # 手动录入的跳过
            if resume.file_url.startswith("manual://"):
                if resume.status != 2:
                    resume.status = 2
                    await resume.save()
                return

            # 2. 标记为处理中
            resume.status = 1
            await resume.save()

            try:
                # 3. 执行解析
                await cls._parse_and_save(resume)

            except Exception as e:
                # 4. 失败标记
                print(f"简历 {resume_id} 解析失败: {e}")
                resume.status = 4
                await resume.save()

    @classmethod
    async def _parse_and_save(cls, resume: Resume):
        """执行解析并保存"""

        # 1. 获取启用的提示词
        prompt = await PromptService.get_active_prompt()
        if not prompt:
            raise ValueError("未配置启用的 Prompt")

        # 2. 下载文件
        file_bytes = await cls._download_pdf(resume.file_url)

        # 3. 解析 PDF
        text_content, avatar_data = PdfParser.parse_pdf(file_bytes)
        if not text_content or len(text_content.strip()) < 10:
            raise ValueError("PDF 文本内容为空")

        # 4. 调用 LLM
        result = await LLMClient.parse_resume(text_content, prompt.content)

        # 5. 保存基本信息
        resume.name = result.get("name")
        resume.phone = result.get("phone")
        resume.email = result.get("email")
        resume.university = result.get("university")
        resume.schooltier = result.get("schooltier")
        resume.degree = result.get("degree")
        resume.major = result.get("major")
        resume.graduation_time = result.get("graduation_year")
        resume.skills = normalize_skills(result.get("skills", []))
        resume.parse_result = result

        # 6. 设置状态
        is_qualified = result.get("is_qualified", False)
        resume.status = 2 if is_qualified else 3

        await resume.save()

        # 7. 同步技能标签
        await cls._sync_skills(resume)

        # 8. 上传头像
        if avatar_data:
            await cls._upload_avatar(resume, avatar_data)

        # 9. 保存评估记录
        await cls._save_evaluation(resume, result, prompt)

    @staticmethod
    async def _download_pdf(file_url: str) -> bytes:
        """从 MinIO 下载文件"""
        # 提取 object_name
        if f"/{MINIO_BUCKET_NAME}/" in file_url:
            object_name = file_url.split(f"/{MINIO_BUCKET_NAME}/")[-1]
        else:
            object_name = file_url.split("/")[-1]

        file_bytes = await MinioClient.get_file_bytes(object_name)
        if not file_bytes:
            raise ValueError("文件下载失败")

        return file_bytes

    @staticmethod
    async def _sync_skills(resume: Resume):
        """同步技能到多对多关系表"""
        skills = await SkillService.get_or_create_skills(resume.skills or [])
        await resume.skill_tags.clear()
        if skills:
            await resume.skill_tags.add(*skills)

    @staticmethod
    async def _upload_avatar(resume: Resume, avatar_data: dict):
        """上传头像"""
        import uuid
        ext = avatar_data["ext"]
        filename = f"avatars/{uuid.uuid4()}.{ext}"

        avatar_url = await MinioClient.upload_bytes(
            avatar_data["bytes"],
            filename,
            f"image/{ext}"
        )

        resume.avatar_url = avatar_url
        await resume.save()

    @staticmethod
    async def _save_evaluation(resume: Resume, result: dict, prompt):
        """保存评估记录"""
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

    # ==================== 查询相关 ====================

    @staticmethod
    async def get_resumes(
        status: Optional[int] = None,
        status_list: Optional[str] = None,
        name: Optional[str] = None,
        university: Optional[str] = None,
        schooltier: Optional[str] = None,
        degree: Optional[str] = None,
        major: Optional[str] = None,
        skill: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
    ):
        """
        多维度简历搜索 - 简化版
        """
        # 基础过滤: 未删除
        query = Resume.filter(is_deleted=0)

        # 状态过滤
        if status_list:
            statuses = [int(s) for s in status_list.replace("[", "").replace("]", "").split(",") if s.strip().isdigit()]
            query = query.filter(status__in=statuses)
        elif status is not None:
            query = query.filter(status=status)

        # 文本字段模糊搜索
        if name:
            query = query.filter(name__icontains=name.strip())
        if university:
            query = query.filter(university__icontains=university.strip())
        if schooltier:
            query = query.filter(schooltier__icontains=schooltier.strip())
        if degree:
            query = query.filter(degree__icontains=degree.strip())
        if major:
            query = query.filter(major__icontains=major.strip())

        # 时间范围
        if date_from:
            query = query.filter(created_at__gte=date_from)
        if date_to:
            query = query.filter(created_at__lte=date_to)

        # 技能搜索 (通过多对多关系)
        if skill:
            skill_terms = [s.strip().lower() for s in skill.replace("，", ",").split(",") if s.strip()]
            for term in skill_terms:
                query = query.filter(skill_tags__name=term)

            results = await query.prefetch_related("skill_tags").order_by("-created_at").distinct()
            return results

        # 普通查询
        return await query.prefetch_related("skill_tags").order_by("-created_at")

    # ==================== 删除相关 ====================

    @staticmethod
    async def delete_resumes_by_info(
        name: Optional[str] = None,
        email: Optional[str] = None,
        phone: Optional[str] = None
    ) -> int:
        """按信息逻辑删除简历"""
        if not any([name, email, phone]):
            return 0

        query = Resume.filter(is_deleted=0)

        if name:
            query = query.filter(name=name)
        if email:
            query = query.filter(email=email)
        if phone:
            query = query.filter(phone=phone)

        resume_ids = await query.values_list('id', flat=True)
        count = len(resume_ids)

        if count > 0:
            await Resume.filter(id__in=resume_ids).update(is_deleted=1)
            await ResumeEvaluation.filter(resume_id__in=resume_ids).delete()

        return count

    # ==================== 批量处理 ====================

    @classmethod
    async def batch_reanalyze_resumes(cls, resume_ids: List[int]):
        """批量重新解析简历"""
        for rid in resume_ids:
            try:
                await cls.process_resume_workflow(rid)
                await asyncio.sleep(1)  # 避免请求过快
            except Exception as e:
                print(f"简历 {rid} 重新解析失败: {e}")

    @staticmethod
    async def get_all_resume_ids() -> List[int]:
        """获取所有有效简历ID"""
        return await Resume.filter(is_deleted=0).values_list("id", flat=True)