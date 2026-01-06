<<<<<<< ours
<<<<<<< ours
from datetime import datetime
from enum import Enum

from sqlalchemy import Column, DateTime, Enum as SqlEnum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()
=======
=======
>>>>>>> theirs
from enum import Enum

from tortoise import fields
from tortoise.models import Model
<<<<<<< ours
>>>>>>> theirs
=======
>>>>>>> theirs


class ResumeStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class PreselectionStatus(str, Enum):
    UNKNOWN = "unknown"
    QUALIFIED = "qualified"
    REJECTED = "rejected"


<<<<<<< ours
<<<<<<< ours
class Resume(Base):
    __tablename__ = "resumes"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    file_url = Column(String(512), nullable=False)
    status = Column(SqlEnum(ResumeStatus), default=ResumeStatus.PENDING, nullable=False)
    preselection_status = Column(
        SqlEnum(PreselectionStatus), default=PreselectionStatus.UNKNOWN, nullable=False
    )
    candidate_name = Column(String(255))
    email = Column(String(255))
    phone = Column(String(64))
    summary = Column(Text)
    avatar_url = Column(String(512))
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    candidate = relationship("Candidate", back_populates="resume", uselist=False)


class Candidate(Base):
    __tablename__ = "candidates"

    id = Column(Integer, primary_key=True, index=True)
    resume_id = Column(Integer, ForeignKey("resumes.id"), nullable=False)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=True)
    phone = Column(String(64), nullable=True)
    avatar_url = Column(String(512), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    resume = relationship("Resume", back_populates="candidate", uselist=False)
=======
=======
>>>>>>> theirs
class Resume(Model):
    id = fields.IntField(pk=True)
    filename = fields.CharField(max_length=255)
    file_url = fields.CharField(max_length=512)
    status = fields.CharEnumField(ResumeStatus, default=ResumeStatus.PENDING)
    preselection_status = fields.CharEnumField(PreselectionStatus, default=PreselectionStatus.UNKNOWN)
    candidate_name = fields.CharField(max_length=255, null=True)
    email = fields.CharField(max_length=255, null=True)
    phone = fields.CharField(max_length=64, null=True)
    summary = fields.TextField(null=True)
    avatar_url = fields.CharField(max_length=512, null=True)
    notes = fields.TextField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    candidate: "Candidate" = fields.ReverseRelation["Candidate"]


class Candidate(Model):
    id = fields.IntField(pk=True)
    resume: fields.ForeignKeyRelation[Resume] = fields.ForeignKeyField(
        "models.Resume", related_name="candidate"
    )
    name = fields.CharField(max_length=255)
    email = fields.CharField(max_length=255, null=True)
    phone = fields.CharField(max_length=64, null=True)
    avatar_url = fields.CharField(max_length=512, null=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)
<<<<<<< ours
>>>>>>> theirs
=======
>>>>>>> theirs
