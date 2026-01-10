# app/utils/helpers.py - 优化版（去正则，简化逻辑）

def normalize_skills(skills):
    """
    标准化技能列表

    优化点：
    1. 去掉类型注解（语法降级）
    2. 简化分隔符处理（不用正则）
    3. 减少中间变量
    """
    if not skills:
        return []

    # 字符串转列表
    if isinstance(skills, str):
        # 统一替换分隔符
        s = skills.replace("，", ",").replace("、", ",").replace("；", ",").replace(";", ",")
        skills = s.split(",")

    # 去重去空
    result = []
    for item in skills:
        s = str(item).strip().lower()
        if s and s not in result:
            result.append(s)

    return result


def extract_year(text):
    """
    提取4位年份

    优化点：
    1. 去掉 Optional 类型注解
    2. 简化逻辑（不用正则）
    """
    if not text:
        return None

    # 提取所有数字
    digits = ""
    for c in str(text):
        if c.isdigit():
            digits += c

    # 找19xx或20xx
    if len(digits) >= 4:
        for i in range(len(digits) - 3):
            year = digits[i:i+4]
            if year.startswith("19") or year.startswith("20"):
                return year

    return None