import uuid
import traceback
import asyncio
import json
from typing import Optional, List
from tortoise.expressions import Q
from app.db.resume_table import Resume
from app.db.candidate_table import Candidate
from app.services.prompt_service import PromptService
from app.utils.minio_client import MinioClient
from app.utils.llm_client import LLMClient
from app.utils.pdf_parser import PdfParser
from app.settings import MINIO_BUCKET_NAME
from app.prompts.base import BasePromptProvider

class ResumeService:
    @staticmethod
    async def create_resume_record(file_url: str) -> Resume:
        """创建简历初始记录"""
        return await Resume.create(file_url=file_url, status=0)

    @staticmethod
    async def process_resume_workflow(resume_id: int,prompt_provider: BasePromptProvider):
        """
        【核心业务逻辑】后台异步执行的任务：PDF解析 + LLM判断 + 结果回写
        """
        print(f"Service: 开始处理简历 {resume_id}")

        # 1. 获取简历记录 (过滤已删除的)
        resume = await Resume.get_or_none(id=resume_id, is_deleted=0)
        if not resume:
            print(f"Service: 未找到有效简历ID {resume_id}")
            return

        # 更新状态为处理中 (1=Processing)
        resume.status = 1
        await resume.save()

        try:
            # 2. 准备环境：获取启用提示词
            prompt_obj = await PromptService.get_active_prompt()
            if not prompt_obj:
                raise Exception("系统未配置启用的提示词 (Prompt)，无法解析")

            # 3. 从 MinIO 下载
            if f"/{MINIO_BUCKET_NAME}/" in resume.file_url:
                object_name = resume.file_url.split(f"/{MINIO_BUCKET_NAME}/")[-1]
            else:
                object_name = resume.file_url.split("/")[-1]

            print(f"正在从 MinIO 下载: {object_name}")
            file_bytes = await MinioClient.get_file_bytes(object_name)
            if not file_bytes:
                raise Exception("文件下载失败或文件内容为空")

            # 4. 解析 PDF
            text_content, avatar_data = PdfParser.parse_pdf(file_bytes)

            if not text_content or len(text_content.strip()) < 10:
                raise Exception("无法从PDF中提取有效文本，请确认简历不是纯图片扫描件")

            # 5. 调用 LLM
            print("正在调用 LLM 进行解析...")
            parse_result = await LLMClient.parse_resume(resume_content=text_content,
                criteria_content=prompt_obj.content,
                prompt_provider=prompt_provider)

            # === 1. 提取数据 ===
            json_data = parse_result.get("json_data", {})
            cand_info = parse_result.get("candidate_info", {})

            def get_edu_field(key):
                return json_data.get("education", {}).get(key)

            # === 2. 更新 Resume 表 ===
            resume.is_qualified = parse_result.get("is_qualified", False)
            resume.parse_result = json_data
            resume.reason = json_data.get("reason")
            resume.prompt = prompt_obj

            resume.name = cand_info.get("name")
            resume.phone = cand_info.get("phone")
            resume.email = cand_info.get("email")

            resume.university = get_edu_field("university")
            resume.schooltier = get_edu_field("schooltier")
            resume.degree = get_edu_field("degree")
            resume.major = get_edu_field("major")
            resume.graduation_time = get_edu_field("graduation_year")

            resume.skills = json_data.get("skills")
            resume.education_history = json_data.get("education_history")

            resume.status = 2 # Completed
            await resume.save()
            print(f"简历解析完成，结果: {'合格' if resume.is_qualified else '不合格'}")

            # 6. 如果是合格候选人，处理头像并创建 Candidate
            if resume.is_qualified:
                # 逻辑删除旧记录 (同一份简历重新解析时，旧的候选人数据逻辑删除)
                old_candidates = await Candidate.filter(resume_id=resume.id, is_deleted=0).all()
                for old_cand in old_candidates:
                    old_cand.is_deleted = 1
                    await old_cand.save()

                avatar_url = None
                if avatar_data:
                    ext = avatar_data['ext']
                    avatar_filename = f"avatars/{uuid.uuid4()}.{ext}"
                    content_type = f"image/{ext}"
                    avatar_url = await MinioClient.upload_bytes(avatar_data['bytes'], avatar_filename, content_type)

                # === 3. 创建 Candidate ===
                await Candidate.create(
                    file_url=resume.file_url,
                    name=cand_info.get("name"),
                    phone=cand_info.get("phone"),
                    email=cand_info.get("email"),
                    avatar_url=avatar_url,
                    university=get_edu_field("university"),
                    schooltier=get_edu_field("schooltier"),
                    degree=get_edu_field("degree"),
                    major=get_edu_field("major"),
                    graduation_time=get_edu_field("graduation_year"),
                    skills=json_data.get("skills"),
                    work_experience=json_data.get("work_experience"),
                    project_experience=json_data.get("projects"),
                    resume=resume,
                    is_deleted=0 # 显式设为0
                )
                print(">>> 合格候选人记录已创建")

        except Exception as e:
            traceback.print_exc()
            print(f"Error: 简历处理流程失败: {str(e)}")
            resume.status = 4 # Failed
            resume.reason = f'解析失败:{str(e)[:500]}'
            await resume.save()

    @staticmethod
    async def get_resumes(
        status: Optional[int] = None,
        is_qualified: Optional[bool] = None,
        name: Optional[str] = None,
        university: Optional[str] = None,
        schooltier: Optional[str] = None,
        degree: Optional[str] = None,
        major: Optional[str] = None,
        skill: Optional[str] = None
    ):
        """多维度简历搜索 (过滤已删除)"""
        # 只查询 is_deleted=0 的
        query = Resume.filter(is_deleted=0)

        if status is not None:
            query = query.filter(status=status)

        if is_qualified is not None:
            query = query.filter(is_qualified=is_qualified)

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
    async def delete_resumes_by_info(
        name: Optional[str] = None,
        email: Optional[str] = None,
        phone: Optional[str] = None
    ) -> int:
        """按自然信息逻辑删除简历"""
        if not any([name, email, phone]):
            return 0

        # 只操作未删除的
        query = Resume.filter(is_deleted=0)

        if name:
            query = query.filter(name=name)
        if email:
            query = query.filter(email=email)
        if phone:
            query = query.filter(phone=phone)

        count = await query.count()
        if count > 0:
            # 逻辑删除：更新状态为 1
            await query.update(is_deleted=1)

        return count

    @staticmethod
    async def batch_reanalyze_resumes(resume_ids: List[int],prompt_provider: BasePromptProvider):
        """批量重新解析简历"""
        print(f"Service: 开始执行批量重测任务，共 {len(resume_ids)} 条...")
        success_count = 0
        fail_count = 0
        for rid in resume_ids:
            try:
                await ResumeService.process_resume_workflow(rid,prompt_provider)
                success_count += 1
                await asyncio.sleep(1)
            except Exception as e:
                print(f"批量任务中 ID {rid} 处理失败: {e}")
                fail_count += 1
        print(f"Service: 批量重测结束。成功 {success_count}，失败 {fail_count}")

    @staticmethod
    async def get_all_resume_ids() -> List[int]:
        """获取所有有效简历ID"""
        return await Resume.filter(is_deleted=0).values_list("id", flat=True)