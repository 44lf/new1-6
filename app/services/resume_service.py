import uuid
import traceback # 用于打印详细报错
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
            
            # 如果没提取到文本 (可能是纯图片扫描件)，且我们还没做 OCR
            if not text_content or len(text_content.strip()) < 10:
                raise Exception("无法从PDF中提取有效文本，请确认简历不是纯图片扫描件")

            # 5. 调用 LLM 进行分析
            print("正在调用 LLM 进行解析...")
            parse_result = await LLMClient.parse_resume(text_content, prompt_obj.content)
            
            # 6. 更新 Resume 表
            is_qualified = parse_result.get("is_qualified", False)
            resume.parse_result = parse_result.get("json_data", {}) # 确保这里字段对应 LLM 返回结构
            resume.is_qualified = is_qualified
            resume.status = 2 # 2=Completed
            await resume.save()
            print(f"简历解析完成，结果: {'合格' if is_qualified else '不合格'}")

            # 7. 如果是合格候选人，处理头像并创建 Candidate
            if is_qualified:
                # 如果这个简历之前已经被识别为候选人，先删除旧记录
                old_candidates = await Candidate.filter(resume_id=resume.id).all()
                for old_cand in old_candidates:
                    print(f"删除旧候选人记录: {old_cand.id}")
                    await old_cand.delete()

                avatar_url = None
                
                # 如果 fitz 提取到了头像，上传到 MinIO
                if avatar_data:
                    ext = avatar_data['ext']
                    # 生成一个新的文件名，防止覆盖，例如: avatars/uuid.png
                    avatar_filename = f"avatars/{uuid.uuid4()}.{ext}"
                    content_type = f"image/{ext}"
                    
                    # 上传头像
                    avatar_url = await MinioClient.upload_bytes(
                        avatar_data['bytes'], 
                        avatar_filename, 
                        content_type
                    )
                    print(f"检测到头像并上传成功: {avatar_url}")

                # 提取 LLM 解析出的候选人基本信息
                # 注意：这里要跟 LLMClient 返回的结构对齐
                cand_info = parse_result.get("candidate_info", {})
                
                # 创建候选人记录
                await Candidate.create(
                    name=cand_info.get("name"),
                    phone=cand_info.get("phone"),
                    email=cand_info.get("email"),
                    avatar_url=avatar_url, # 存入刚才上传的头像 URL
                    resume=resume
                )
                print(">>> 合格候选人记录已创建")

        except Exception as e:
            # 打印完整的错误堆栈，方便调试
            traceback.print_exc()
            print(f"Error: 简历处理流程失败: {str(e)}")
            
            resume.status = 4 # 4=Failed
            # 也可以把错误信息存个字段，方便前端展示
            await resume.save()