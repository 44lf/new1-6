from tortoise import fields, models

class Prompt(models.Model):
    id = fields.IntField(pk=True)
    
    # 给提示词起个名，比如 "初级工程师筛选版", "高级经理筛选版"
    name = fields.CharField(max_length=50)
    
    # 具体的提示词内容，很长
    content = fields.TextField()
    
    # 是否启用。逻辑上我们只允许一个是 True，其他的都是 False
    is_active = fields.BooleanField(default=False)
    
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "prompts"

