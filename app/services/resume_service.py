import uuid
import traceback # 用于打印详细报错
from typing import Optional
from tortoise.expressions import Q
from app.db.resume_table import Resume
from app.db.candidate_table import Candidate
from app.services.prompt_service import PromptService
from app.utils.minio_client import MinioClient
from app.utils.llm_client import LLMClient
from app.utils.pdf_parser import PdfParser
from app.settings import MINIO_BUCKET_NAME # <--- 【修复】新增导入

class ResumeService:
    @staticmethod
    async def create_resume_record(file_url: str) -> Resume:
        """创建简历初始记录"""
        # 0=Pending
        return await Resume.create(file_url=file_url, status=0) 

    @staticmethod
    async def process_resume_workflow(resume_id: int):
        """
        【核心业务逻辑】后台异步执行的任务：PDF解析 + LLM判断 + 结果回写
        """
        print(f"Service: 开始处理简历 {resume_id}")
        
        # 1. 获取简历记录
        resume = await Resume.get_or_none(id=resume_id)
        if not resume:
            print(f"Service: 未找到简历ID {resume_id}")
            return

        # 更新状态为处理中 (1=Processing)
        resume.status = 1 
        await resume.save()

        try:
            # 2. 准备环境：获取启用提示词
            prompt_obj = await PromptService.get_active_prompt()
            if not prompt_obj:
                raise Exception("系统未配置启用的提示词 (Prompt)，无法解析")

            # 3. 从 MinIO 下载二进制文件
            # 逻辑：从完整 URL 中提取 object_name。
            # 假设 file_url 格式如: http://127.0.0.1:9000/resumes/2023/file.pdf
            # split 之后取最后一部分作为文件名，但这可能不够严谨。
            # 更稳妥的方式是在 create_resume_record 时直接存 object_name，这里先兼容处理：
            if f"/{MINIO_BUCKET_NAME}/" in resume.file_url:
                object_name = resume.file_url.split(f"/{MINIO_BUCKET_NAME}/")[-1]
            else:
                # 容错：如果 URL 格式不对，直接尝试用 URL 最后一段
                object_name = resume.file_url.split("/")[-1]
            
            print(f"正在从 MinIO 下载: {object_name}")
            file_bytes = await MinioClient.get_file_bytes(object_name)
            if not file_bytes:
                raise Exception("文件下载失败或文件内容为空")

            # 4. 使用 fitz (PyMuPDF) 解析 PDF
            text_content, avatar_data = PdfParser.parse_pdf(file_bytes)

            print(f"DEBUG - 提取到的文本内容 (前200字): {text_content[:200]}")

            # 如果没提取到文本 (可能是纯图片扫描件)，且我们还没做 OCR
            if not text_content or len(text_content.strip()) < 10:
                raise Exception("无法从PDF中提取有效文本，请确认简历不是纯图片扫描件")

            # 5. 调用 LLM 进行分析
            print("正在调用 LLM 进行解析...")
            parse_result = await LLMClient.parse_resume(text_content, prompt_obj.content)

            import json
            print(f"DEBUG - LLM 解析结果: {json.dumps(parse_result, ensure_ascii=False)}")

            # === 1. 提取数据 (这是你缺少的步骤) ===
            json_data = parse_result.get("json_data", {})
            cand_info = parse_result.get("candidate_info", {})

            # 辅助函数：防止 json_data 里没有 education 字段导致报错
            def get_edu_field(key):
                return json_data.get("education", {}).get(key)

            # === 2. 更新 Resume 表 (这是你缺少的步骤) ===
            resume.is_qualified = parse_result.get("is_qualified", False)
            resume.parse_result = json_data
            resume.reason = json_data.get("reason")

            # 【关键修复A】必须把 prompt_obj 存入，否则无法按岗位筛选！
            resume.prompt = prompt_obj

            # 【关键修复B】把基础信息填入 Resume 表的新字段
            resume.name = cand_info.get("name")
            resume.phone = cand_info.get("phone")
            resume.email = cand_info.get("email")

            resume.university = get_edu_field("university")
            resume.major = get_edu_field("major")
            resume.graduation_time = get_edu_field("graduation_year")

            # 复杂结构建议由 Prompt 保证返回列表，或者在这里做类型检查
            resume.skills = json_data.get("skills")
            resume.education_history = json_data.get("education_history") # 需Prompt配合

            resume.status = 2 # Completed
            await resume.save()
            print(f"简历解析完成，结果: {'合格' if resume.is_qualified else '不合格'}")

            # 7. 如果是合格候选人，处理头像并创建 Candidate
            if resume.is_qualified:
                # 删除旧记录逻辑 (保持不变)
                old_candidates = await Candidate.filter(resume_id=resume.id).all()
                for old_cand in old_candidates:
                    await old_cand.delete()

                avatar_url = None
                # 头像上传逻辑 (保持不变)
                if avatar_data:
                    # ... (原有的上传代码) ...
                    ext = avatar_data['ext']
                    avatar_filename = f"avatars/{uuid.uuid4()}.{ext}"
                    content_type = f"image/{ext}"
                    avatar_url = await MinioClient.upload_bytes(avatar_data['bytes'], avatar_filename, content_type)

                # === 3. 创建 Candidate (这是你缺少的步骤) ===
                # 【关键修复C】这里必须把 skills, experience 等详细数据存进去
                await Candidate.create(
                    # 基础信息
                    name=cand_info.get("name"),
                    phone=cand_info.get("phone"),
                    email=cand_info.get("email"),
                    avatar_url=avatar_url,

                    # 核心能力 (新加的字段)
                    university=get_edu_field("university"),
                    major=get_edu_field("major"),
                    graduation_time=get_edu_field("graduation_year"),
                    skills=json_data.get("skills"),

                    # 详细经历 (新加的字段)
                    work_experience=json_data.get("work_experience"),
                    project_experience=json_data.get("projects"),

                    resume=resume
                )
                print(">>> 合格候选人记录已创建 (包含完整详情)")


        except Exception as e:
            # 打印完整的错误堆栈，方便调试
            traceback.print_exc()
            print(f"Error: 简历处理流程失败: {str(e)}")
            
            resume.status = 4 # 4=Failed
            # 也可以把错误信息存个字段，方便前端展示
            resume.reason = f'解析失败:{str(e)[:500]}'
            await resume.save()

    @staticmethod
    async def get_resumes(
        status: Optional[int] = None,
        is_qualified: Optional[bool] = None,
        name: Optional[str] = None,
        university: Optional[str] = None,
        major: Optional[str] = None,
        skill: Optional[str] = None
    ):
        query = Resume.all()

        # 1. 基础状态筛选
        if status is not None:
            query = query.filter(status=status)

        if is_qualified is not None:
            query = query.filter(is_qualified=is_qualified)

        # 2. 内容模糊搜索 (模拟 HR 的搜索习惯)
        if name:
            # 搜索简历解析出的姓名
            query = query.filter(name__icontains=name)

        if university:
            query = query.filter(university__icontains=university)

        if major:
            query = query.filter(major__icontains=major)

        # 3. 技能搜索 (JSON 字段搜索)
        if skill:
            query = query.filter(skills__icontains=skill)

        return await query.order_by("-created_at")

    @staticmethod
    async def delete_resumes_by_info(
        name: Optional[str] = None,
        email: Optional[str] = None,
        phone: Optional[str] = None
    ) -> int:
        """
        按自然信息删除简历
        """
        if not any([name, email, phone]):
            return 0

        query = Resume.all()

        # 精确匹配，防止误删
        if name:
            query = query.filter(name=name)
        if email:
            query = query.filter(email=email)
        if phone:
            query = query.filter(phone=phone)

        count = await query.count()
        if count > 0:
            # 注意：如果数据库设置了级联删除(CASCADE)，
            # 这里的删除操作也会自动删除关联的 Candidate 记录
            await query.delete()

        return count