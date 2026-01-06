import base64
import io
from datetime import datetime
from typing import Optional

from fastapi import BackgroundTasks, UploadFile
from sqlalchemy.orm import Session

from app.config import settings
from app.db import models
from app.db.database import SessionLocal
from app.models.resume import ResumeCreateResponse
from app.services.llm_client import LLMService
from app.services.minio_client import MinioService


class ResumeService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.minio = MinioService()
        self.llm = LLMService()

    def create_resume_entry(self, filename: str, file_url: str) -> models.Resume:
        resume = models.Resume(filename=filename, file_url=file_url)
        self.db.add(resume)
        self.db.commit()
        self.db.refresh(resume)
        return resume

    async def upload_and_process(
        self, background_tasks: BackgroundTasks, file: UploadFile, prompt: Optional[str] = None
    ) -> ResumeCreateResponse:
        file_bytes = await file.read()
        buffer = io.BytesIO(file_bytes)
        file_url = self.minio.upload_file(buffer, file.filename, file.content_type or "application/octet-stream")
        resume = self.create_resume_entry(filename=file.filename, file_url=file_url)

        background_tasks.add_task(self._process_resume, resume.id, file_bytes, prompt)

        return ResumeCreateResponse.from_orm(resume)

    async def _process_resume(self, resume_id: int, file_bytes: bytes, prompt: Optional[str]) -> None:
        with SessionLocal() as db:
            resume = db.get(models.Resume, resume_id)
            if resume is None:
                return

            resume.status = models.ResumeStatus.PROCESSING
            resume.updated_at = datetime.utcnow()
            db.commit()

            try:
                resume_text = file_bytes.decode("utf-8", errors="ignore")
                prompt_text = prompt or "请根据以下简历判断候选人是否满足岗位基础要求，并返回结构化数据。"
                llm_result = await self.llm.analyze_resume(resume_text, prompt_text)
                await self._handle_llm_result(db, resume, llm_result)
            except Exception as exc:  # noqa: BLE001
                resume.status = models.ResumeStatus.FAILED
                resume.notes = str(exc)
                resume.updated_at = datetime.utcnow()
                db.commit()

    async def _handle_llm_result(self, db: Session, resume: models.Resume, result: dict) -> None:
        resume.candidate_name = result.get("name")
        resume.email = result.get("email")
        resume.phone = result.get("phone")
        resume.summary = result.get("summary")
        resume.notes = result.get("notes")

        qualified = bool(result.get("qualified"))
        resume.preselection_status = (
            models.PreselectionStatus.QUALIFIED if qualified else models.PreselectionStatus.REJECTED
        )
        resume.status = models.ResumeStatus.COMPLETED
        resume.updated_at = datetime.utcnow()

        avatar_url = await self._maybe_upload_avatar(result.get("avatar"))
        resume.avatar_url = avatar_url

        if qualified:
            self._create_candidate(db, resume, avatar_url)

        db.commit()

    async def _maybe_upload_avatar(self, avatar_data: Optional[str]) -> Optional[str]:
        if not avatar_data:
            return None

        try:
            content = base64.b64decode(avatar_data)
        except Exception:  # noqa: BLE001
            return None

        filename = f"avatars/{datetime.utcnow().timestamp()}.png"
        return self.minio.upload_bytes(content, filename, "image/png")

    def _create_candidate(self, db: Session, resume: models.Resume, avatar_url: Optional[str]) -> None:
        candidate = models.Candidate(
            resume_id=resume.id,
            name=resume.candidate_name or resume.filename,
            email=resume.email,
            phone=resume.phone,
            avatar_url=avatar_url,
        )
        db.add(candidate)
