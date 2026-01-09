from pydantic import BaseModel, Field, EmailStr, validator
from typing import List, Optional
from app.enums.education import SchoolTier, Degree

class CandidateCreate(BaseModel):

    # 1. 基础信息
    name: str = Field(..., min_length=2, max_length=50, description="候选人姓名")
    phone: str = Field(..., description="联系电话")
    email: Optional[EmailStr] = Field(None, description="邮箱地址")

    # 2. 教育背景 (直接使用枚举类型，Pydantic 会自动校验值是否在枚举范围内)
    university: Optional[str] = Field(None, description="毕业院校")
    schooltier: Optional[SchoolTier] = Field(None, description="学校层次")
    degree: Optional[Degree] = Field(None, description="学历")
    major: Optional[str] = Field(None, description="专业")
    graduation_time: Optional[str] = Field(None, description="毕业年份，建议输入4位数字")

    # 3. 列表字段
    skills: List[str] = Field(default=[], description="技能标签列表")
    work_experience: List[str] = Field(default=[], description="工作经历列表")
    project_experience: List[str] = Field(default=[], description="项目经历列表")

    prompt_id: int = Field(..., description="关联岗位ID")


    @validator('phone')
    def validate_phone(cls, v):
        """
        校验手机号 (纯逻辑判断)
        规则：11位数字，以1开头
        """
        # 1. 检查长度
        if len(v) != 11:
            raise ValueError('手机号长度必须为11位')

        # 2. 检查是否纯数字
        if not v.isdigit():
            raise ValueError('手机号必须由纯数字组成')

        # 3. 检查开头 (简单判断以1开头，如果需要更严谨可以判断第二位)
        if not v.startswith('1'):
            raise ValueError('手机号格式不正确')

        return v

    @validator('graduation_time')
    def validate_year(cls, v):
        """
        清洗毕业年份 (列表推导式提取数字)
        输入 "2024年" -> 输出 "2024"
        """
        if not v:
            return v

        # 提取字符串中所有的数字字符
        digits = [char for char in v if char.isdigit()]

        # 如果连4个数字都凑不齐，说明格式不对
        if len(digits) < 4:
            # 或者你可以选择在这里抛错，看业务需求
            return v

        # 取前4位数字拼接，当作年份 (例如 "2024.06" -> "2024")
        year_str = "".join(digits[:4])

        # 简单校验一下年份是否合理 (比如 1900-2100)
        year_int = int(year_str)
        if not (1900 <= year_int <= 2100):
             raise ValueError('毕业年份看似不合理，请检查')

        return year_str
