from tortoise import fields, models

class Resume(models.Model):
    # 主键 ID，自动生成的
    id = fields.IntField(pk=True)
    
    # 存 MinIO 返回的文件地址
    file_url = fields.CharField(max_length=255, description="简历文件URL")
    
    # 状态：0=未处理, 1=处理中, 2=合格, 3=不合格, 4=失败
    # 给个默认值 0，因为刚上传肯定是未处理
    status = fields.IntField(default=0, description="处理状态")
    
    # 存大模型解析出来的全部原始数据，用 JSON 存最灵活
    # null=True 表示刚创建时可以是空的
    parse_result = fields.JSONField(null=True, description="AI解析结果")
    
    # 是否合格，方便快速筛选
    is_qualified = fields.BooleanField(default=False, description="是否合格")
    
    # 记录上传时间，auto_now_add=True 表示创建时自动填当前时间
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "resumes" # 数据库里的表名
        ordering = ["-created_at"] # 默认按时间倒序排（最新的在前面）