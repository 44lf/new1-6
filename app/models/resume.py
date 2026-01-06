from datetime import datetime
from typing import Optional

from pydantic import BaseModel, HttpUrl

from app.db.models import PreselectionStatus, ResumeStatus


class ResumeCreateResponse(BaseModel):
    id: int
    filename: str
    file_url: HttpUrl
    status: ResumeStatus
    preselection_status: PreselectionStatus
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
<<<<<<< ours
=======
        from_attributes = True
>>>>>>> theirs


class ResumeDetail(BaseModel):
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
<<<<<<< ours
=======
    notes: Optional[str]
>>>>>>> theirs
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
<<<<<<< ours
=======
        from_attributes = True
>>>>>>> theirs
