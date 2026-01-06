from datetime import datetime
from typing import Optional

<<<<<<< ours
from pydantic import BaseModel, HttpUrl


class CandidateResponse(BaseModel):
=======
from pydantic import BaseModel, ConfigDict, HttpUrl


class CandidateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

>>>>>>> theirs
    id: int
    resume_id: int
    name: str
    email: Optional[str]
    phone: Optional[str]
    avatar_url: Optional[HttpUrl]
    created_at: datetime
    updated_at: datetime
<<<<<<< ours

    class Config:
        orm_mode = True
<<<<<<< ours
=======
        from_attributes = True
>>>>>>> theirs
=======
>>>>>>> theirs
