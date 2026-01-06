from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, HttpUrl


class CandidateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    resume_id: int
    name: str
    email: Optional[str]
    phone: Optional[str]
    avatar_url: Optional[HttpUrl]
    created_at: datetime
    updated_at: datetime
