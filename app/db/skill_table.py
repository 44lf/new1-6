from tortoise import fields, models


class Skill(models.Model):
    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=100, unique=True, description="技能名称")
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "skills"
