# 3달, 1년, 5년 전체 차트 조회

import requests
from bs4 import BeautifulSoup

# 주가 조회
def get_current_price(code: str) -> str:
    url = f"https://finance.naver.com/item/main.naver?code={code}"
    headers = {"User-Agent": "Mozilla/5.0"}
    res = requests.get(url, headers=headers)
    soup = BeautifulSoup(res.text, "html.parser")

    try:
        price = soup.select_one("p.no_today span.blind").text
        return price
    except Exception:
        return "조회 실패"

# 상한가, 하한가 조회
def get_price_summary(code: str) -> dict:
    url = f"https://finance.naver.com/item/main.naver?code={code}"
    headers = {"User-Agent": "Mozilla/5.0"}
    res = requests.get(url, headers=headers)
    soup = BeautifulSoup(res.text, "html.parser")

    def get_text(selector):
        el = soup.select_one(selector)
        return el.text.strip().replace(",", "") if el else None

    name = get_text("div.wrap_company h2 a")
    current_price = get_text("p.no_today span.blind")

    em_tags = soup.select("em.no_cha")
    if len(em_tags) >= 2:
        high_spans = em_tags[0].find_all("span")
        low_spans = em_tags[1].find_all("span")

        high_limit = "".join(s.text for s in high_spans if s.text.strip().isdigit())
        low_limit = "".join(s.text for s in low_spans if s.text.strip().isdigit())
    else:
        high_limit = None
        low_limit = None

    if not current_price or not high_limit or not low_limit:
        return {
            "error": "크롤링 실패",
            "detail": f"current: {current_price}, high: {high_limit}, low: {low_limit}"
        }

    return {
        "code": code,
        "name": name,
        "current": f"{int(current_price):,}",
        "high_limit": f"{int(high_limit):,}",
        "low_limit": f"{int(low_limit):,}",
    }

# 차트 조회 
def get_daily_stock_data(stock_code: str, page: int = 1):
    url = f"https://finance.naver.com/item/sise_day.naver?code={stock_code}&page={page}"
    headers = {
        "User-Agent": "Mozilla/5.0"
    }
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")

    table = soup.select_one("table.type2")
    if not table:
        return []

    rows = table.select("tr")
    temp_data = []

    for row in rows:
        cols = row.select("td")
        if len(cols) >= 7:
            date = cols[0].text.strip()
            close = cols[1].text.strip().replace(",", "")
            open_price = cols[3].text.strip().replace(",", "")
            high = cols[4].text.strip().replace(",", "")
            low = cols[5].text.strip().replace(",", "")
            volume = cols[6].text.strip().replace(",", "")

            if date and close and open_price and high and low and volume:
                try:
                    temp_data.append({
                        "date": date,
                        "end": int(close),
                        "start": int(open_price),
                        "high": int(high),
                        "low": int(low),
                        "trading_volume": int(volume),
                    })
                except ValueError:
                    # 만약 데이터가 비정상 (예: 하이픈 '-' 같은 경우)이면 무시
                    continue

    # 여기서 등락률 계산
    data_list = []
    for i in range(len(temp_data) - 1):  # 마지막은 전일 종가가 없으니 제외
        today = temp_data[i]
        yesterday = temp_data[i + 1]

        try:
            prev_close = yesterday["종가"]
            fluctuation_rate = round(((today["종가"] - prev_close) / prev_close) * 100, 2)
        except ZeroDivisionError:
            fluctuation_rate = None

        today["등락률"] = fluctuation_rate
        data_list.append(today)

    return data_list