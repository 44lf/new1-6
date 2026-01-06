from enum import Enum

from tortoise import fields
from tortoise.models import Model


class ResumeStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class PreselectionStatus(str, Enum):
    UNKNOWN = "unknown"
    QUALIFIED = "qualified"
    REJECTED = "rejected"


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
