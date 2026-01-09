import asyncio
from datetime import datetime
from typing import List, Optional
from tortoise.expressions import Q

from app.db.resume_table import Resume
from app.db.resume_evaluation_table import ResumeEvaluation
from app.services.prompt_service import PromptService
from app.services.skill_service import SkillService
from app.utils.minio_client import MinioClient
from app.utils.llm_client import LLMClient
from app.utils.pdf_parser import PdfParser
from app.utils.skill_utils import normalize_text_value, parse_skill_terms, normalize_skills_lower
from app.settings import MINIO_BUCKET_NAME


class ResumeService:
    """简历处理服务"""
    _sem = asyncio.Semaphore(3)

    # ==================== 核心业务流程 ====================
    
    @staticmethod
    async def create_resume_record(file_url: str) -> Resume:
        """创建简历初始记录"""
        return await Resume.create(file_url=file_url, status=0)

    @classmethod
    async def process_resume_workflow(cls, resume_id: int):
        """
        【核心流程】后台异步解析简历
        流程: 获取简历 → 下载文件 → 解析PDF → 调用LLM → 保存结果
        """
        async with cls._sem:
            resume = await cls._get_valid_resume(resume_id)
            if not resume:
                return
            
            if cls._is_manual_entry(resume):
                await cls._ensure_qualified_status(resume)
                return
            
            resume.status = 1
            await resume.save(update_fields=["status"])
            
            try:
                await cls._execute_parsing(resume)
            except Exception as e:
                await cls._handle_parsing_failure(resume, e)

    # ==================== 核心解析逻辑 ====================
    
    @classmethod
    async def _execute_parsing(cls, resume: Resume):
        """执行完整的解析流程"""
        prompt = await PromptService.get_active_prompt()
        if not prompt:
            raise ValueError("未配置启用的 Prompt")
        
        file_bytes = await cls._download_file(resume.file_url)
        text_content, avatar_data = PdfParser.parse_pdf(file_bytes)
        
        if not text_content or len(text_content.strip()) < 10:
            raise ValueError("PDF 文本内容为空或过短")
        
        parse_result = await LLMClient.parse_resume(text_content, prompt.content)
        await cls._save_parsing_results(resume, parse_result, avatar_data, prompt)

    @staticmethod
    async def _download_file(file_url: str) -> bytes:
        """从 MinIO 下载文件"""
        if f"/{MINIO_BUCKET_NAME}/" in file_url:
            object_name = file_url.split(f"/{MINIO_BUCKET_NAME}/")[-1]
        else:
            object_name = file_url.split("/")[-1]
        
        file_bytes = await MinioClient.get_file_bytes(object_name)
        
        if not file_bytes:
            raise ValueError("文件下载失败或内容为空")
        
        return file_bytes

    @classmethod
    async def _save_parsing_results(
        cls,
        resume: Resume,
        parse_result: dict,
        avatar_data: Optional[dict],
        prompt
    ):
        """保存解析结果到数据库"""
        json_data = parse_result.get("json_data", {})
        cand_info = parse_result.get("candidate_info", {})
        edu = json_data.get("education", {})
        
        resume.parse_result = json_data
        resume.name = cand_info.get("name")
        resume.phone = cand_info.get("phone")
        resume.email = cand_info.get("email")
        
        resume.university = edu.get("university")
        resume.schooltier = edu.get("schooltier")
        resume.degree = edu.get("degree")
        resume.major = edu.get("major")
        resume.graduation_time = edu.get("graduation_year")
        resume.education_history = json_data.get("education_history")
        
        resume.skills = normalize_skills_lower(json_data.get("skills", []))
        
        is_qualified = parse_result.get("is_qualified", False)
        resume.status = 2 if is_qualified else 3
        
        await resume.save()
        await cls._sync_skill_tags(resume)
        
        if avatar_data:
            await cls._upload_avatar(resume, avatar_data)
        
        await cls._save_evaluation(resume, parse_result, prompt)

    @staticmethod
    async def _sync_skill_tags(resume: Resume):
        """同步技能标签到多对多关系"""
        resume_skills = await SkillService.get_or_create_skills(resume.skills or [])
        await resume.skill_tags.clear()
        if resume_skills:
            await resume.skill_tags.add(*resume_skills)

    @staticmethod
    async def _upload_avatar(resume: Resume, avatar_data: dict):
        """上传头像到 MinIO"""
        import uuid
        ext = avatar_data["ext"]
        filename = f"avatars/{uuid.uuid4()}.{ext}"
        content_type = f"image/{ext}"
        
        avatar_url = await MinioClient.upload_bytes(
            avatar_data["bytes"],
            filename,
            content_type
        )
        
        resume.avatar_url = avatar_url
        await resume.save(update_fields=["avatar_url"])

    @staticmethod
    async def _save_evaluation(resume: Resume, parse_result: dict, prompt):
        """保存评估记录"""
        json_data = parse_result.get("json_data", {})
        is_qualified = parse_result.get("is_qualified", False)
        
        await ResumeEvaluation.update_or_create(
            defaults={
                "score": json_data.get("score"),
                "is_qualified": is_qualified,
                "reason": json_data.get("reason"),
                "evaluated_at": datetime.utcnow(),
            },
            resume=resume,
            prompt=prompt,
        )

    # ==================== 辅助方法 ====================
    
    @staticmethod
    async def _get_valid_resume(resume_id: int) -> Optional[Resume]:
        """获取有效的简历记录"""
        return await Resume.get_or_none(id=resume_id, is_deleted=0)

    @staticmethod
    def _is_manual_entry(resume: Resume) -> bool:
        """判断是否为手动录入"""
        return resume.file_url and resume.file_url.startswith("manual://")

    @staticmethod
    async def _ensure_qualified_status(resume: Resume):
        """确保手动录入的简历状态为已完成"""
        if resume.status != 2:
            resume.status = 2
            await resume.save(update_fields=["status"])

    @staticmethod
    async def _handle_parsing_failure(resume: Resume, error: Exception):
        """处理解析失败"""
        resume.status = 4
        await resume.save(update_fields=["status"])

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
        """多维度简历搜索"""
        filters = Q(is_deleted=0)
        
        # 标准化输入
        normalized_name = normalize_text_value(name)
        normalized_university = normalize_text_value(university)
        normalized_schooltier = normalize_text_value(schooltier)
        normalized_degree = normalize_text_value(degree)
        normalized_major = normalize_text_value(major)
        skill_terms = parse_skill_terms(skill)
        
        # 构建过滤条件
        if status_list:
            filters &= Q(status__in=_parse_status_list(status_list))
        elif status is not None:
            filters &= Q(status=status)
        
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
        if date_from:
            filters &= Q(created_at__gte=date_from)
        if date_to:
            filters &= Q(created_at__lte=date_to)
        
        # 查询
        query = Resume.filter(filters).prefetch_related("skill_tags")
        
        # 技能过滤（多对多关系）
        if skill_terms:
            for term in skill_terms:
                query = query.filter(skill_tags__name=term)
            return await query.order_by("-created_at").distinct()
        
        return await query.order_by("-created_at")

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
                await asyncio.sleep(1)
            except Exception:
                pass

    @staticmethod
    async def get_all_resume_ids() -> List[int]:
        """获取所有有效简历ID"""
        return await Resume.filter(is_deleted=0).values_list("id", flat=True)


# ==================== 工具函数 ====================

def _parse_status_list(status_list: str) -> list[int]:
    """解析状态列表字符串"""
    allowed = {0, 1, 2, 3, 4}
    statuses = []
    current = []
    
    for char in status_list:
        if char.isdigit():
            current.append(char)
        elif current:
            statuses.append(int("".join(current)))
            current = []
    
    if current:
        statuses.append(int("".join(current)))
    
    if not statuses:
        raise ValueError("未找到有效状态值")
    
    invalid = [s for s in statuses if s not in allowed]
    if invalid:
        raise ValueError(f"无效状态值: {invalid}")
    
    return list(dict.fromkeys(statuses))