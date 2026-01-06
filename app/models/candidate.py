from datetime import datetime
from typing import Optional

from pydantic import BaseModel, HttpUrl


class CandidateResponse(BaseModel):
    id: int
    resume_id: int
    name: str
    email: Optional[str]
    phone: Optional[str]
    avatar_url: Optional[HttpUrl]
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
<<<<<<< ours
=======
        from_attributes = True
>>>>>>> theirs
