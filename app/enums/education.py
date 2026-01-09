from enum import Enum

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