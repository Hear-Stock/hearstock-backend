import requests
from bs4 import BeautifulSoup
from app.api.kiwoomREST import get_kiwoom_token, get_kiwoom_stkinfo


# 업종 PER, 등락률 조회
def get_industry_per(code: str):
    url = f"https://finance.naver.com/item/main.naver?code={code}"
    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    try:
        res = requests.get(url, headers=headers, timeout=5)
        res.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"[요청 오류] {e}")
        return {"per": None, "change_rate": None, "error": "request failed"}

    try:
        soup = BeautifulSoup(res.text, "html.parser")
        table = soup.find("table", summary="동일업종 PER 정보")

        if not table:
            return {"per": None, "change_rate": None, "error": "table not found"}
        # 테이블에서 <td> 요소 추출
        tds = table.find_all("td")
        if len(tds) < 2:
            return {"per": None, "change_rate": None, "error": "insufficient data"}
        # PER, 등락률 추출해서 return
        return {
            "per": tds[0].text.strip(),
            "change_rate": tds[1].text.strip(),
            "error": None
        }

    except Exception as e:
        return {"per": None, "change_rate": None}



