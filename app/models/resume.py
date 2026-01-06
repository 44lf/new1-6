from datetime import datetime
from typing import Optional

<<<<<<< ours
from pydantic import BaseModel, HttpUrl
=======
from pydantic import BaseModel, ConfigDict, HttpUrl
>>>>>>> theirs

from app.db.models import PreselectionStatus, ResumeStatus


class ResumeCreateResponse(BaseModel):
<<<<<<< ours
=======
    model_config = ConfigDict(from_attributes=True)

>>>>>>> theirs
    id: int
    filename: str
    file_url: HttpUrl
    status: ResumeStatus
    preselection_status: PreselectionStatus
    created_at: datetime
    updated_at: datetime

<<<<<<< ours
    class Config:
        orm_mode = True
<<<<<<< ours
=======
        from_attributes = True
>>>>>>> theirs


class ResumeDetail(BaseModel):
=======

class ResumeDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)

>>>>>>> theirs
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
=======
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime
>>>>>>> theirs
