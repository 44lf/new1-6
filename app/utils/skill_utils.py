from typing import Optional


def normalize_skills_lower(skills: list[str]) -> list[str]:
    """标准化技能列表为小写"""
    if not skills:
        return []
    return [s.strip().lower() for s in skills if s and s.strip()]


def normalize_skill_query(skill: str) -> str:
    """将技能查询词标准化为小写"""
    return skill.strip().lower()


def normalize_text_value(value: Optional[str]) -> Optional[str]:
    """标准化文本值"""
    if value is None:
        return None
    normalized = value.strip()
    return normalized or None


def parse_skill_terms(skill: Optional[str]) -> list[str]:
    if not skill:
        return []

    normalized = skill.strip().replace("，", ",").replace("、", ",")
    comma_parts = normalized.split(",")

    tokens = []
    for part in comma_parts:
        space_parts = part.split()
        tokens.extend(space_parts)

    result = []
    for token in tokens:
        cleaned = token.strip()
        if cleaned:
            result.append(normalize_skill_query(cleaned))

    return result
