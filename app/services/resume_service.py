import asyncio
import traceback
import uuid
from datetime import datetime
from typing import List, Optional
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
    #同时限制LLM解析数量
    _sem = asyncio.Semaphore(3)

    @staticmethod
    async def create_resume_record(file_url: str) -> Resume:
        """创建简历初始记录"""
        return await Resume.create(file_url=file_url, status=0)

    @classmethod
    async def process_resume_workflow(cls, resume_id: int,prompt_provider: BasePromptProvider):
        async with cls._sem:
            """
            【核心业务逻辑】后台异步执行的任务：PDF解析 + LLM判断 + 结果回写
            """
            print(f"Service: 开始处理简历 {resume_id} (获得并发锁)")

            # 1. 获取简历记录 (过滤已删除的)
            resume = await Resume.get_or_none(id=resume_id, is_deleted=0)
            if not resume:
                print(f"Service: 未找到有效简历ID {resume_id}")
                return

            if resume.file_url and resume.file_url.startswith("manual://"):
                print(f"Service: 简历 {resume_id} 为手动录入数据，跳过 AI 解析流程")
                # 确保状态为合格/完成，避免卡在“处理中”
                if resume.status != 2:
                    resume.status = 2
                    await resume.save()
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
                resume.score = json_data.get('score')

                resume.name = cand_info.get("name")
                resume.phone = cand_info.get("phone")
                resume.email = cand_info.get("email")

                resume.university = get_edu_field("university")
                resume.schooltier = get_edu_field("schooltier")
                resume.degree = get_edu_field("degree")
                resume.major = get_edu_field("major")
                resume.graduation_time = get_edu_field("graduation_year")

                resume.skills = normalize_skills_lower(json_data.get("skills"))
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
                        prompt=prompt_obj,
                        score=json_data.get('score'),
                        name=cand_info.get("name"),
                        phone=cand_info.get("phone"),
                        email=cand_info.get("email"),
                        avatar_url=avatar_url,
                        university=get_edu_field("university"),
                        schooltier=get_edu_field("schooltier"),
                        degree=get_edu_field("degree"),
                        major=get_edu_field("major"),
                        graduation_time=get_edu_field("graduation_year"),
                        skills=normalize_skills_lower(json_data.get("skills")),
                        work_experience=json_data.get("work_experience"),
                        project_experience=json_data.get("projects"),
                        resume=resume,
                        parse_result=json_data,
                        is_deleted=0 # 显式设为0
                    )
                    print(">>> 合格候选人记录已创建")
                print(f"Service: 简历 {resume_id} 处理完毕，释放锁")

            except Exception as e:
                traceback.print_exc()
                print(f"Error: 简历处理流程失败: {str(e)}")
                resume.status = 4 # Failed
                resume.reason = f'解析失败:{str(e)[:500]}'
                await resume.save()

    @staticmethod
    async def get_resumes(
        status: Optional[int] = None,
        status_list: Optional[str] = None,
        is_qualified: Optional[bool] = None,
        name: Optional[str] = None,
        university: Optional[str] = None,
        schooltier: Optional[str] = None,
        degree: Optional[str] = None,
        major: Optional[str] = None,
        skill: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
    ):
        """多维度简历搜索 (过滤已删除)"""
        filters = Q(is_deleted=0)
        normalized_name = normalize_text_value(name)
        normalized_university = normalize_text_value(university)
        normalized_schooltier = normalize_text_value(schooltier)
        normalized_degree = normalize_text_value(degree)
        normalized_major = normalize_text_value(major)
        skill_terms = parse_skill_terms(skill)

        if status_list is not None:
            parsed_statuses = parse_status_list(status_list)
            filters &= Q(status__in=parsed_statuses)
        elif status is not None:
            filters &= Q(status=status)

        if is_qualified is not None:
            filters &= Q(is_qualified=is_qualified)

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

        # 技能查询优化 - 先查询后过滤
        query = Resume.filter(filters)

        if skill_terms:
            # 获取所有符合前置条件的简历
            all_resumes = await query.all()

            # Python层面过滤技能
            filtered_resumes = []
            for resume in all_resumes:
                if not resume.skills:
                    continue

                # 将简历的技能列表转为小写
                resume_skills_lower = [s.lower() if isinstance(s, str) else str(s).lower()
                                      for s in resume.skills]

                # 检查是否所有搜索技能都在简历技能中
                if all(term.lower() in resume_skills_lower for term in skill_terms):
                    filtered_resumes.append(resume)

            return filtered_resumes
        else:
            # 没有技能过滤,直接返回
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

        resume_ids = await query.values_list('id', flat=True)
        count = len(resume_ids)

        if count > 0:
            # 1. 逻辑删除简历
            await Resume.filter(id__in=resume_ids).update(is_deleted=1)

            # 2. 同步逻辑删除关联的候选人 (Candidate)
            # 只有当候选人关联的 resume_id 在我们删除的列表中时才删除
            await Candidate.filter(resume_id__in=resume_ids, is_deleted=0).update(is_deleted=1)

            print(f"已逻辑删除 {count} 份简历及其关联的候选人记录")
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


def normalize_skills_lower(skills: list[str]) -> list[str]:
    """标准化技能列表为小写"""
    if not skills:
        return []
    return [s.strip().lower() for s in skills if s and s.strip()]


def normalize_skill_query(skill: str) -> str:
    """将技能查询词标准化为小写"""
    return skill.strip().lower()


def normalize_text_value(value: Optional[str]) -> Optional[str]:
    """标准化文本值"""
    if value is None:
        return None
    normalized = value.strip()
    return normalized or None


def parse_skill_terms(skill: Optional[str]) -> list[str]:

    if not skill:
        return []

    # 1. 统一分隔符：将中文逗号和顿号替换为英文逗号
    normalized = skill.strip().replace('，', ',').replace('、', ',')

    # 2. 先按逗号分割
    comma_parts = normalized.split(',')

    # 3. 再按空格分割每个部分
    tokens = []
    for part in comma_parts:
        # 按空格分割
        space_parts = part.split()
        tokens.extend(space_parts)

    # 4. 清理并转小写
    result = []
    for token in tokens:
        cleaned = token.strip()
        if cleaned:
            result.append(normalize_skill_query(cleaned))

    return result


def parse_status_list(status_list: Optional[str]) -> list[int]:
    """解析状态列表字符串，提取数字并校验范围"""
    if status_list is None:
        return []

    allowed_statuses = {0, 1, 2, 3, 4}
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

    invalid_statuses = [status for status in statuses if status not in allowed_statuses]
    if invalid_statuses:
        raise ValueError("存在无效状态值")

    unique_statuses = []
    for status in statuses:
        if status not in unique_statuses:
            unique_statuses.append(status)

    return unique_statuses
