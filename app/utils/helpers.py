# app/utils/helpers.py
"""
通用工具函数 - 合并了 skill_utils 的功能
"""
from typing import Optional, List


# ==================== 技能处理 ====================

def normalize_skills(skills) -> List[str]:
    """
    标准化技能列表为小写
    支持: 列表、字符串(逗号分隔)、None
    """
    if not skills:
        return []

    # 如果是字符串，先转成列表
    if isinstance(skills, str):
        # 统一替换各种分隔符为逗号
        normalized = skills.replace("，", ",").replace("、", ",").replace("；", ",").replace(";", ",")
        skills = normalized.split(",")

    # 去空格、转小写、去重
    result = []
    for s in skills:
        s = str(s).strip().lower()
        if s and s not in result:
            result.append(s)

    return result


# ==================== 文本标准化 ====================

def normalize_text(text: Optional[str]) -> Optional[str]:
    """标准化文本: 去空格，空字符串转 None"""
    if not text:
        return None
    normalized = text.strip()
    return normalized if normalized else None


def extract_year(text: Optional[str]) -> Optional[str]:
    """
    从文本中提取4位年份
    例如: "2024年7月" -> "2024"
    """
    if not text:
        return None

    # 提取所有数字
    digits = "".join(c for c in str(text) if c.isdigit())

    # 找到19xx或20xx开头的4位数字
    if len(digits) >= 4:
        for i in range(len(digits) - 3):
            year = digits[i:i+4]
            if year.startswith("19") or year.startswith("20"):
                return year

    return None
