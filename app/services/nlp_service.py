# 자연어 처리 api

PERIOD_MAP = {
    "일주일": 7,
    "1주": 7,
    "한주": 7,
    "한달": 30,
    "1개월": 30,
    "3개월": 90,
    "1년": 365,
    "3년": 1095,
    "5년": 1825
}

def extract_period(text: str) -> int | None:
    for key, value in PERIOD_MAP.items():
        if key in text:
            return value
    if "전체" in text:
        return -1  
    return None
