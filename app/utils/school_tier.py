from __future__ import annotations

from typing import Optional

TIER_985_211 = {
    "清华大学",
    "北京大学",
    "复旦大学",
    "上海交通大学",
    "浙江大学",
    "南京大学",
    "中国科学技术大学",
    "哈尔滨工业大学",
    "西安交通大学",
    "北京航空航天大学",
    "北京理工大学",
    "中国人民大学",
    "武汉大学",
    "华中科技大学",
    "中山大学",
    "同济大学",
    "天津大学",
    "东南大学",
    "南开大学",
    "四川大学",
    "厦门大学",
}

TIER_DOUBLE_FIRST_CLASS = {
    "中国科学院大学",
    "南方科技大学",
    "上海科技大学",
    "北京邮电大学",
    "北京交通大学",
    "南京航空航天大学",
    "南京理工大学",
    "西北工业大学",
    "西北大学",
    "电子科技大学",
    "重庆大学",
    "吉林大学",
    "山东大学",
    "中南大学",
    "华东师范大学",
    "华南理工大学",
    "东北大学",
    "华东理工大学",
    "苏州大学",
    "北京科技大学",
}

ALIAS_MAP = {
    "清华": "清华大学",
    "北大": "北京大学",
    "复旦": "复旦大学",
    "上交": "上海交通大学",
    "上交大": "上海交通大学",
    "浙大": "浙江大学",
    "南大": "南京大学",
    "中科大": "中国科学技术大学",
    "哈工大": "哈尔滨工业大学",
    "西交": "西安交通大学",
    "北航": "北京航空航天大学",
    "北理": "北京理工大学",
    "人大": "中国人民大学",
    "武大": "武汉大学",
    "华科": "华中科技大学",
    "中大": "中山大学",
    "同济": "同济大学",
    "天大": "天津大学",
    "东大": "东南大学",
    "南开": "南开大学",
    "川大": "四川大学",
    "厦大": "厦门大学",
    "国科大": "中国科学院大学",
}


def _normalize_name(name: str) -> str:
    return (
        name.strip()
        .replace(" ", "")
        .replace("\u3000", "")
        .replace("（", "(")
        .replace("）", ")")
    )


def _canonical_name(university: str) -> str:
    normalized = _normalize_name(university)
    return ALIAS_MAP.get(normalized, normalized)


def infer_school_tier(university: Optional[str]) -> Optional[str]:
    if not university:
        return None

    name = _canonical_name(university)

    if name in TIER_985_211:
        return "985/211"

    if name in TIER_DOUBLE_FIRST_CLASS:
        return "双一流"

    for canonical, full_name in ALIAS_MAP.items():
        if canonical in name or full_name in name:
            if full_name in TIER_985_211:
                return "985/211"
            if full_name in TIER_DOUBLE_FIRST_CLASS:
                return "双一流"

    return None
