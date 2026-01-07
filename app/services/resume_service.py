from app.db.resume_table import Resume
from app.db.candidate_table import Candidate
from app.services.prompt_service import PromptService
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