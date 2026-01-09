from tortoise import fields, models

class Candidate(models.Model):
    id = fields.IntField(pk=True)
    #系统状态，0=正常, 1=已删除
    is_deleted = fields.IntField(default=0, description="逻辑删除状态，0=正常, 1=已删除")

    #关联岗位
    prompt = fields.ForeignKeyField('models.Prompt', related_name=False, null=True, description="关联的岗位提示词")

    #关联分数
    score = fields.IntField(null=True, description='AI判断岗位契合度分数')

    #简历基础信息
    name = fields.CharField(max_length=50, null=True)
    phone = fields.CharField(max_length=20, null=True)
    email = fields.CharField(max_length=100, null=True)
    
    file_url = fields.CharField(max_length=255, description="简历文件URL")
    avatar_url = fields.CharField(max_length=255, null=True, description="头像URL")

    #教育背景
    university = fields.CharField(max_length=100, null=True, description="毕业院校")
    schooltier = fields.CharField(max_length=50, null=True, description="学校层次")
    degree = fields.CharField(max_length=50, null=True, description="学历")
    major = fields.CharField(max_length=100, null=True, description="专业")
    graduation_time = fields.CharField(max_length=50, null=True, description="毕业时间/年份")
    education_history = fields.JSONField(null=True, description="完整教育经历列表") # 备用，如果有多段教育

    #技能
    skills = fields.JSONField(null=True, description="技能标签列表，如 ['Python', 'Vue']")

    #工作经历
    work_experience = fields.JSONField(null=True, description="工作经历列表")

    #项目
    project_experience = fields.JSONField(null=True, description="项目经验列表")

    resume = fields.ForeignKeyField('models.Resume', related_name='candidate')

    parse_result = fields.JSONField(null=True, description="AI解析结果")

    selection_time = fields.DatetimeField(auto_now_add=True)
    created_at = fields.DatetimeField(auto_now_add=True, description="候选人创建时间")

    class Meta:
        table = "candidates"
