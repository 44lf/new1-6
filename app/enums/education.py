from enum import Enum
from typing import Optional, Iterable, List, Set


SCHOOL_ALIASES = {
    "北大": "北京大学",
    "清华": "清华大学",
    "上交": "上海交通大学",
    "复旦": "复旦大学",
    "浙大": "浙江大学",
    "中科大": "中国科学技术大学",
    "人大": "中国人民大学",
    "南大": "南京大学",
    "武大": "武汉大学",
    "华科": "华中科技大学",
    "厦大": "厦门大学",
    "同济": "同济大学",
    "北航": "北京航空航天大学",
    "北理": "北京理工大学",
    "中山": "中山大学",
    "华南理工": "华南理工大学",
    "上财": "上海财经大学",
}

SCHOOL_ALIAS_MAP = {}
for alias, canonical in SCHOOL_ALIASES.items():
    SCHOOL_ALIAS_MAP.setdefault(canonical, set()).add(alias)

SCHOOL_TIER_985 = {
    "清华大学",
    "北京大学",
    "中国人民大学",
    "北京航空航天大学",
    "北京理工大学",
    "北京师范大学",
    "中国农业大学",
    "中央民族大学",
    "南开大学",
    "天津大学",
    "大连理工大学",
    "东北大学",
    "吉林大学",
    "哈尔滨工业大学",
    "复旦大学",
    "同济大学",
    "上海交通大学",
    "华东师范大学",
    "南京大学",
    "东南大学",
    "浙江大学",
    "中国科学技术大学",
    "厦门大学",
    "山东大学",
    "中国海洋大学",
    "武汉大学",
    "华中科技大学",
    "中南大学",
    "湖南大学",
    "中山大学",
    "华南理工大学",
    "四川大学",
    "电子科技大学",
    "重庆大学",
    "西安交通大学",
    "西北工业大学",
    "兰州大学",
    "西北农林科技大学",
    "国防科技大学",
}

SCHOOL_TIER_211 = {
    "北京交通大学",
    "北京工业大学",
    "北京科技大学",
    "北京化工大学",
    "北京邮电大学",
    "北京林业大学",
    "北京中医药大学",
    "北京外国语大学",
    "中国传媒大学",
    "中央财经大学",
    "对外经济贸易大学",
    "中国政法大学",
    "华北电力大学",
    "中国矿业大学",
    "中国石油大学",
    "中国地质大学",
    "辽宁大学",
    "东北师范大学",
    "延边大学",
    "哈尔滨工程大学",
    "东北农业大学",
    "东北林业大学",
    "华东理工大学",
    "东华大学",
    "上海大学",
    "上海财经大学",
    "上海外国语大学",
    "上海海事大学",
    "南京航空航天大学",
    "南京理工大学",
    "南京农业大学",
    "河海大学",
    "南京师范大学",
    "中国药科大学",
    "苏州大学",
    "江南大学",
    "合肥工业大学",
    "福州大学",
    "南昌大学",
    "华中农业大学",
    "华中师范大学",
    "中南财经政法大学",
    "武汉理工大学",
    "西南交通大学",
    "西南财经大学",
    "西南大学",
    "广西大学",
    "贵州大学",
    "云南大学",
    "西北大学",
    "陕西师范大学",
    "长安大学",
    "西北农林科技大学",
    "中国人民大学",
    "北京师范大学",
    "南京大学",
    "东南大学",
    "湖南大学",
    "中南大学",
    "中山大学",
    "华南理工大学",
    "四川大学",
    "电子科技大学",
    "重庆大学",
    "西安交通大学",
    "西北工业大学",
    "兰州大学",
    "厦门大学",
    "山东大学",
    "中国海洋大学",
    "吉林大学",
    "东北大学",
    "大连理工大学",
    "哈尔滨工业大学",
    "同济大学",
    "上海交通大学",
    "复旦大学",
    "浙江大学",
    "中国科学技术大学",
    "武汉大学",
    "华中科技大学",
    "北京理工大学",
    "北京航空航天大学",
    "南开大学",
    "天津大学",
    "清华大学",
    "北京大学",
}

SCHOOL_TIER_DOUBLE_FIRST = {
    "北京邮电大学",
    "北京交通大学",
    "北京科技大学",
    "北京化工大学",
    "北京工业大学",
    "北京林业大学",
    "北京中医药大学",
    "中国政法大学",
    "中国传媒大学",
    "中央财经大学",
    "对外经济贸易大学",
    "上海财经大学",
    "上海外国语大学",
    "上海大学",
    "华东理工大学",
    "东华大学",
    "南京航空航天大学",
    "南京理工大学",
    "南京农业大学",
    "河海大学",
    "南京师范大学",
    "中国药科大学",
    "苏州大学",
    "江南大学",
    "合肥工业大学",
    "福州大学",
    "南昌大学",
    "华中农业大学",
    "华中师范大学",
    "中南财经政法大学",
    "武汉理工大学",
    "西南交通大学",
    "西南财经大学",
    "西南大学",
    "广西大学",
    "贵州大学",
    "云南大学",
    "西北大学",
    "陕西师范大学",
    "长安大学",
    "东北师范大学",
    "延边大学",
}

JUNIOR_KEYWORDS = (
    "职业技术学院",
    "职业学院",
    "高等专科学校",
    "高等专科",
    "专科学校",
    "专科",
    "职业大学",
)

ORDINARY_KEYWORDS = ("大学", "学院")

class SchoolTier(str, Enum):
    c985 = "985"
    c211 = "211"
    first_class = "双一流"
    ordinary = "普通本科"
    junior = "专科"
    null = "null"


class Degree(str, Enum):
    phd = "博士"
    master = "硕士"
    bachelor = "本科"
    junior = "大专"
    null = "null"


def normalize_school_tier(value: Optional[object]) -> Optional[SchoolTier]:
    if value is None:
        return None
    if isinstance(value, SchoolTier):
        return value
    text = str(value).strip()
    if not text:
        return None
    if text == "null":
        return SchoolTier.null
    if "985" in text:
        return SchoolTier.c985
    if "211" in text:
        return SchoolTier.c211
    if "双一流" in text:
        return SchoolTier.first_class
    if "普通本科" in text or "本科" in text:
        return SchoolTier.ordinary
    if "专科" in text or "大专" in text:
        return SchoolTier.junior
    try:
        return SchoolTier(text)
    except ValueError:
        return None


def normalize_university_name(university: Optional[str]) -> Optional[str]:
    if not university:
        return None
    cleaned = str(university).strip().replace(" ", "")
    return SCHOOL_ALIASES.get(cleaned, cleaned)


def expand_university_query(university: Optional[str]) -> List[str]:
    if not university:
        return []
    normalized = normalize_university_name(university)
    terms = {str(university).strip(), normalized}
    if normalized in SCHOOL_ALIAS_MAP:
        terms.update(SCHOOL_ALIAS_MAP[normalized])
    return [term for term in terms if term]


def _strip_suffixes(name: str, suffixes: Iterable[str]) -> str:
    for suffix in suffixes:
        if name.endswith(suffix):
            return name[: -len(suffix)]
    return name


def _matches_school_set(name: str, school_set: Set[str]) -> bool:
    if name in school_set:
        return True
    base = _strip_suffixes(name, ("大学", "学院", "学校", "分校"))
    if base and base != name:
        if base in school_set:
            return True
        if f"{base}大学" in school_set:
            return True
        if f"{base}学院" in school_set:
            return True
    return False


def infer_school_tier(university: Optional[str]) -> Optional[SchoolTier]:
    if not university:
        return None
    normalized = normalize_university_name(university)
    if not normalized:
        return None
    if "985" in normalized:
        return SchoolTier.c985
    if "211" in normalized:
        return SchoolTier.c211
    if _matches_school_set(normalized, SCHOOL_TIER_985):
        return SchoolTier.c985
    if _matches_school_set(normalized, SCHOOL_TIER_211):
        return SchoolTier.c211
    if _matches_school_set(normalized, SCHOOL_TIER_DOUBLE_FIRST):
        return SchoolTier.first_class
    if any(keyword in normalized for keyword in JUNIOR_KEYWORDS):
        return SchoolTier.junior
    if any(keyword in normalized for keyword in ORDINARY_KEYWORDS):
        return SchoolTier.ordinary
    return None
