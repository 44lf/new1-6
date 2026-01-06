import base64
from datetime import datetime
from typing import Optional

import fitz
from fastapi import BackgroundTasks, UploadFile

from app.config import settings
from app.db import models
from app.models.resume import ResumeCreateResponse
from app.services.llm_client import LLMService
from app.services.minio_client import MinioService


class ResumeService:
    def __init__(self) -> None:
        self.minio = MinioService()
        self.llm = LLMService()

    async def upload_and_process(
        self, background_tasks: BackgroundTasks, file: UploadFile, prompt: Optional[str] = None
    ) -> ResumeCreateResponse:
        file_bytes = await file.read()
        file_url = await self.minio.upload_file(file_bytes, file.filename, file.content_type or "application/pdf")

        resume = await models.Resume.create(filename=file.filename, file_url=file_url)
        response = ResumeCreateResponse.model_validate(resume, from_attributes=True)

        background_tasks.add_task(self._process_resume, resume.id, file_bytes, prompt)

        return response

    async def _process_resume(self, resume_id: int, file_bytes: bytes, prompt: Optional[str]) -> None:
        try:
            resume = await models.Resume.get(id=resume_id)
        except models.Resume.DoesNotExist:  # type: ignore[attr-defined]
            return

        resume.status = models.ResumeStatus.PROCESSING
        await resume.save()

        try:
            resume_text = self._extract_text(file_bytes)
            llm_result = await self.llm.analyze_resume(resume_text, prompt or settings.default_prompt)
            await self._handle_llm_result(resume, llm_result)
        except Exception as exc:  # noqa: BLE001
            resume.status = models.ResumeStatus.FAILED
            resume.notes = str(exc)
            await resume.save()

    async def _handle_llm_result(self, resume: models.Resume, result: dict) -> None:
        qualified = bool(result.get("qualified"))
        avatar_data = result.get("avatar")
        avatar_url = await self._maybe_upload_avatar(avatar_data) if avatar_data else None

        resume.candidate_name = result.get("name")
        resume.email = result.get("email")
        resume.phone = result.get("phone")
        resume.summary = result.get("summary")
        resume.notes = result.get("notes")
        resume.preselection_status = (
            models.PreselectionStatus.QUALIFIED if qualified else models.PreselectionStatus.REJECTED
        )
        resume.status = models.ResumeStatus.COMPLETED
        resume.avatar_url = avatar_url
        resume.updated_at = datetime.utcnow()
        await resume.save()

        if qualified:
            await models.Candidate.get_or_create(
                resume=resume,
                defaults={
                    "name": resume.candidate_name or resume.filename,
                    "email": resume.email,
                    "phone": resume.phone,
                    "avatar_url": avatar_url,
                },
            )

    async def _maybe_upload_avatar(self, avatar_data: str) -> Optional[str]:
        try:
            content = base64.b64decode(avatar_data)
        except Exception:  # noqa: BLE001
            return None

        filename = f"avatars/{datetime.utcnow().timestamp()}.png"
        return await self.minio.upload_file(content, filename, "image/png")

    def _extract_text(self, file_bytes: bytes) -> str:
        try:
            with fitz.open(stream=file_bytes, filetype="pdf") as doc:
                return "\n".join(page.get_text() for page in doc)
        except Exception:
            # Fallback to raw text decode
            return file_bytes.decode("utf-8", errors="ignore")
