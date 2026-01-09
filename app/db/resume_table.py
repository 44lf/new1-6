from tortoise import fields, models

class Resume(models.Model):
    # 主键 ID，自动生成的
    id = fields.IntField(pk=True)
    #系统状态，0=正常, 1=已删除
    is_deleted = fields.IntField(default=0, description="逻辑删除状态，0=正常, 1=已删除")

    # 存 MinIO 返回的文件地址
    file_url = fields.CharField(max_length=255, description="简历文件URL")
    avatar_url = fields.CharField(max_length=255, null=True, description="头像URL")

    # 状态：0=未处理, 1=处理中, 2=合格, 3=不合格, 4=失败
    # 给个默认值 0
    status = fields.IntField(default=0, description="处理状态")

    #简历基础内容
    name = fields.CharField(max_length=50, null=True, description='姓名')
    phone = fields.CharField(max_length=50, null=True, description="联系电话")
    email = fields.CharField(max_length=100, null=True, description="邮箱")

    #教育背景
    university = fields.CharField(max_length=100, null=True, description="毕业院校")
    schooltier = fields.CharField(max_length=50, null=True, description="学校层次")
    degree = fields.CharField(max_length=50, null=True, description="学历")
    major = fields.CharField(max_length=100, null=True, description="专业")
    graduation_time = fields.CharField(max_length=50, null=True, description="毕业时间/年份")
    education_history = fields.JSONField(null=True, description="完整教育经历列表") # 备用，如果有多段教育

    #技能
    skills = fields.JSONField(null=True, description="技能标签列表，如 ['Python', 'Vue']")
    skill_tags: fields.ManyToManyRelation["Skill"] = fields.ManyToManyField(
        "models.Skill",
        related_name="resumes",
        through="resume_skills",
    )
    # 存大模型解析出来的全部原始数据，用 JSON 存最灵活
    # null=True 表示刚创建时可以是空的
    parse_result = fields.JSONField(null=True, description="AI解析结果")
    
    # 记录上传时间，auto_now_add=True 表示创建时自动填当前时间
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "resumes" # 数据库里的表名
        ordering = ["-created_at"] # 默认按时间倒序排（最新的在前面）
