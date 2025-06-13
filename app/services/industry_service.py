import requests
from bs4 import BeautifulSoup

def get_industry_info(code: str):
    url = f"https://finance.naver.com/item/main.naver?code={code}"
    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    try:
        res = requests.get(url, headers=headers, timeout=5)
        res.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"[요청 오류] {e}")
        return {
            "market_rank": None,
            "opinion": None,
            "target_price": None,
            "industry_per": None,
            "industry_rate": None,
            "error": "request failed"
        }

    try:
        soup = BeautifulSoup(res.text, "html.parser")

        # 1. 시가총액 순위
        try:
            table = soup.find("table", summary="시가총액 정보")
            tds = table.find_all("td") if table else []
            market_rank = tds[1].get_text(strip=True) if len(tds) > 1 else None
        except Exception:
            market_rank = None

        # 2. 투자의견 및 목표주가
        try:
            table = soup.find("table", summary="투자의견 정보")
            tds = table.find_all("td") if table else []
            if len(tds) > 0:
                opinion_span = tds[0].find("span", class_="f_up")
                investment_opinion = opinion_span.get_text(strip=True) if opinion_span else None
                em_tags = tds[0].find_all("em")
                target_price = em_tags[-1].get_text(strip=True).replace(",", "") if em_tags else None
            else:
                investment_opinion = None
                target_price = None
        except Exception:
            investment_opinion = None
            target_price = None

        # 3. 동일업종 PER 정보 및 등락률
        try:
            table = soup.find("table", summary="동일업종 PER 정보")
            tds = table.find_all("td") if table else []
            industry_per = tds[0].get_text(strip=True) if len(tds) > 0 else None
            change_rate = tds[1].get_text(strip=True) if len(tds) > 1 else None
        except Exception:
            industry_per = None
            change_rate = None

        return {
            "market_rank": market_rank,
            "opinion": investment_opinion,
            "target_price": target_price,
            "industry_per": industry_per,
            "industry_rate": change_rate
        }

    except Exception as e:
        print(f"[파싱 오류] {e}")
        return {
            "market_rank": None,
            "opinion": None,
            "target_price": None,
            "industry_per": None,
            "industry_rate": None,
            "error": "parse failed"
        }


# 실행 예시
if __name__ == "__main__":
    result = get_industry_info("005930")  # 삼성전자
    print(result)
