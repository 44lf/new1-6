# app/utils/helpers.py
"""
通用工具函数 - 合并了 skill_utils 和 school_tier 的功能
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


# ==================== 学校层次推断 ====================

# 985/211 学校关键词 (只列常见的，不用太全)
TIER_985_211 = [
    "清华", "北大", "复旦", "上交", "浙大", "南大", "中科大",
    "哈工大", "西交", "北航", "北理", "人大", "武大", "华科",
    "中山", "同济", "天大", "东南", "南开", "川大", "厦大"
]

# 双一流学校关键词
TIER_DOUBLE_FIRST = [
    "国科大", "南科大", "上科大", "北邮", "北交", "南航", "南理工",
    "西工大", "电子科大", "重大", "吉大", "山大", "中南", "华东师大",
    "华南理工", "东北大学", "华理", "苏大", "北科"
]


def infer_school_tier(university: Optional[str]) -> Optional[str]:
    """
    根据学校名称推断层次
    返回: "985/211" | "双一流" | None
    """
    if not university:
        return None

    # 去掉空格，统一格式
    name = university.strip().replace(" ", "").replace("大学", "")

    # 检查 985/211
    for keyword in TIER_985_211:
        if keyword in name:
            return "985/211"

    # 检查双一流
    for keyword in TIER_DOUBLE_FIRST:
        if keyword in name:
            return "双一流"

    return None


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