from tortoise import fields, models


class ResumeEvaluation(models.Model):
    id = fields.IntField(pk=True)
    resume = fields.ForeignKeyField(
        "models.Resume",
        related_name="evaluations",
        description="关联简历",
    )
    prompt = fields.ForeignKeyField(
        "models.Prompt",
        related_name="resume_evaluations",
        description="关联的岗位提示词",
    )
    score = fields.IntField(null=True, description="AI判断岗位契合度分数")
    is_qualified = fields.BooleanField(default=False, description="是否合格")
    reason = fields.TextField(null=True, description="AI判断合格/不合格的理由")
    evaluated_at = fields.DatetimeField(auto_now_add=True, description="评估时间")

    class Meta:
        table = "resume_evaluations"
        unique_together = (("resume", "prompt"),)
