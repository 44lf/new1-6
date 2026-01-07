from app.db.resume_table import Resume
from app.db.candidate_table import Candidate
from app.services.prompt_service import PromptService
import uuid
from app.utils.minio_client import MinioClient
from app.utils.llm_client import LLMClient
from app.utils.pdf_parser import PdfParser


# 假设的工具类导入
# from app.utils.llm_client import LLMClient 
# from app.utils.minio_client import MinioClient 

class ResumeService:
    @staticmethod
    async def create_resume_record(file_url: str) -> Resume:
        """创建简历初始记录"""
        return await Resume.create(file_url=file_url, status=0) # 0=Pending

    @staticmethod
    async def process_resume_workflow(resume_id: int):
        """
        【核心业务逻辑】后台异步执行的任务
        """
        print(f"Service: 开始处理简历 {resume_id}")
        resume = await Resume.get_or_none(id=resume_id)
        if not resume:
            return

        # 1. 更新状态为处理中
        resume.status = 1 # Processing
        await resume.save()

        try:
            # 2. 获取 Prompt
            prompt_obj = await PromptService.get_active_prompt()
            if not prompt_obj:
                raise Exception("没有启用的提示词，无法解析")

            # 3. 读取文件内容 (伪代码)
            # file_content = await MinioClient.get_text(resume.file_url)
            file_content = "模拟的简历文本内容..." 

            # 4. 调用 LLM (伪代码)
            # parse_data = await LLMClient.parse(content=file_content, prompt=prompt_obj.content)
            
            # --- 模拟 LLM 返回结果 ---
            parse_data = {
                "is_qualified": True,
                "json_data": {"name": "张三", "skills": ["Python"]},
                "candidate_info": {"name": "张三", "phone": "13800138000", "email": "zhang@abc.com"}
            }
            # -----------------------

            # 5. 更新简历结果
            resume.parse_result = parse_data["json_data"]
            resume.is_qualified = parse_data["is_qualified"]
            resume.status = 2 # Completed
            await resume.save()

            # 6. 如果合格，触发候选人生成逻辑
            if resume.is_qualified:
                await ResumeService._create_candidate_from_resume(resume, parse_data["candidate_info"])

        except Exception as e:
            print(f"处理失败: {e}")
            resume.status = 4 # Failed
            await resume.save()

    @staticmethod
    async def _create_candidate_from_resume(resume: Resume, info: dict):
        """
        内部私有方法：合格后生成候选人
        """
        # 这里可能还涉及下载头像上传 MinIO 的逻辑，建议封装在 Service 内部
        await Candidate.create(
            name=info.get("name"),
            phone=info.get("phone"),
            email=info.get("email"),
            resume=resume
        )
    @staticmethod
    async def process_resume_workflow(resume_id: int):
        """
        后台任务：PDF解析 + LLM判断 + 结果回写
        """
        print(f"Service: 开始处理简历 {resume_id}")
        resume = await Resume.get_or_none(id=resume_id)
        if not resume:
            return

        resume.status = 1 # Processing
        await resume.save()

        try:
            # 1. 准备环境：获取 Prompt
            prompt_obj = await PromptService.get_active_prompt()
            if not prompt_obj:
                raise Exception("未找到启用的提示词")

            # 2. 【核心变化】从 MinIO 下载二进制文件
            # 假设 resume.file_url 存的是完整URL，我们需要提取 object_name
            # 这里简化处理，假设你存的时候 file_url 就是 "resumes/xxx.pdf" 或者是完整 URL 需要截取
            # 为了方便，建议存入库的时候直接保留 object_name，或者这里解析一下
            object_name = resume.file_url.split(f"/{MinioClient.MINIO_BUCKET_NAME}/")[-1]
            
            file_bytes = await MinioClient.get_file_bytes(object_name)
            if not file_bytes:
                raise Exception("文件下载失败或文件为空")

            # 3. 【核心变化】使用 fitz 解析 PDF
            text_content, avatar_data = PdfParser.parse_pdf(file_bytes)
            
            if not text_content:
                raise Exception("无法从PDF中提取文本，可能是纯图片扫描件")

            # 4. 调用 LLM 进行分析
            parse_result = await LLMClient.parse_resume(text_content, prompt_obj.content)
            
            # 5. 更新 Resume 表
            is_qualified = parse_result.get("is_qualified", False)
            resume.parse_result = parse_result.get("json_data", {})
            resume.is_qualified = is_qualified
            resume.status = 2 # Completed
            await resume.save()

            # 6. 【核心变化】如果是合格候选人，处理头像并创建 Candidate
            if is_qualified:
                avatar_url = None
                
                # 如果 fitz 提取到了头像，上传到 MinIO
                if avatar_data:
                    ext = avatar_data['ext']
                    # 生成一个新的文件名，避免覆盖
                    avatar_filename = f"avatars/{uuid.uuid4()}.{ext}"
                    content_type = f"image/{ext}"
                    
                    # 上传头像
                    avatar_url = await MinioClient.upload_bytes(
                        avatar_data['bytes'], 
                        avatar_filename, 
                        content_type
                    )
                    print(f"头像上传成功: {avatar_url}")

                # 提取 LLM 解析出的候选人基本信息
                cand_info = parse_result.get("candidate_info", {})
                
                # 创建候选人记录
                await Candidate.create(
                    name=cand_info.get("name"),
                    phone=cand_info.get("phone"),
                    email=cand_info.get("email"),
                    avatar_url=avatar_url, # 存入刚才上传的头像 URL
                    resume=resume
                )
                print("合格候选人记录创建成功")

        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"处理失败: {e}")
            resume.status = 4 # Failed
            await resume.save()