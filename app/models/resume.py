from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, HttpUrl

from app.db.models import PreselectionStatus, ResumeStatus


class ResumeCreateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    filename: str
    file_url: HttpUrl
    status: ResumeStatus
    preselection_status: PreselectionStatus
    created_at: datetime
    updated_at: datetime

class ResumeDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    filename: str
    file_url: HttpUrl
    status: ResumeStatus
    preselection_status: PreselectionStatus
    candidate_name: Optional[str]
    email: Optional[str]
    phone: Optional[str]
    summary: Optional[str]
    avatar_url: Optional[str]
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime
