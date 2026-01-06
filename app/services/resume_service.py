import base64
<<<<<<< ours
<<<<<<< ours
import io
from datetime import datetime
from typing import Optional

from fastapi import BackgroundTasks, UploadFile
from sqlalchemy.orm import Session

from app.config import settings
from app.db import models
from app.db.database import SessionLocal
=======
=======
>>>>>>> theirs
from datetime import datetime
from typing import Optional

import fitz
from fastapi import BackgroundTasks, UploadFile

from app.config import settings
from app.db import models
<<<<<<< ours
>>>>>>> theirs
=======
>>>>>>> theirs
from app.models.resume import ResumeCreateResponse
from app.services.llm_client import LLMService
from app.services.minio_client import MinioService


class ResumeService:
<<<<<<< ours
<<<<<<< ours
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

=======
=======
>>>>>>> theirs
    def __init__(self) -> None:
        self.minio = MinioService()
        self.llm = LLMService()

<<<<<<< ours
>>>>>>> theirs
=======
>>>>>>> theirs
    async def upload_and_process(
        self, background_tasks: BackgroundTasks, file: UploadFile, prompt: Optional[str] = None
    ) -> ResumeCreateResponse:
        file_bytes = await file.read()
<<<<<<< ours
<<<<<<< ours
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
=======
=======
>>>>>>> theirs
        file_url = await self.minio.upload_file(file_bytes, file.filename, file.content_type or "application/pdf")

        resume = await models.Resume.create(filename=file.filename, file_url=file_url)
        response = ResumeCreateResponse.from_orm(resume)

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

<<<<<<< ours
>>>>>>> theirs
=======
>>>>>>> theirs
        resume.candidate_name = result.get("name")
        resume.email = result.get("email")
        resume.phone = result.get("phone")
        resume.summary = result.get("summary")
        resume.notes = result.get("notes")
<<<<<<< ours
<<<<<<< ours

        qualified = bool(result.get("qualified"))
=======
>>>>>>> theirs
=======
>>>>>>> theirs
        resume.preselection_status = (
            models.PreselectionStatus.QUALIFIED if qualified else models.PreselectionStatus.REJECTED
        )
        resume.status = models.ResumeStatus.COMPLETED
<<<<<<< ours
<<<<<<< ours
        resume.updated_at = datetime.utcnow()

        avatar_url = await self._maybe_upload_avatar(result.get("avatar"))
        resume.avatar_url = avatar_url

        if qualified:
            self._create_candidate(db, resume, avatar_url)

        db.commit()

    async def _maybe_upload_avatar(self, avatar_data: Optional[str]) -> Optional[str]:
        if not avatar_data:
            return None

=======
=======
>>>>>>> theirs
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
<<<<<<< ours
>>>>>>> theirs
=======
>>>>>>> theirs
        try:
            content = base64.b64decode(avatar_data)
        except Exception:  # noqa: BLE001
            return None

        filename = f"avatars/{datetime.utcnow().timestamp()}.png"
<<<<<<< ours
<<<<<<< ours
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
=======
=======
>>>>>>> theirs
        return await self.minio.upload_file(content, filename, "image/png")

    def _extract_text(self, file_bytes: bytes) -> str:
        try:
            with fitz.open(stream=file_bytes, filetype="pdf") as doc:
                return "\n".join(page.get_text() for page in doc)
        except Exception:
            # Fallback to raw text decode
            return file_bytes.decode("utf-8", errors="ignore")
<<<<<<< ours
>>>>>>> theirs
=======
>>>>>>> theirs
