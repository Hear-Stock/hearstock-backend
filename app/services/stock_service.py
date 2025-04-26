import requests
import pandas as pd
from io import StringIO
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
def get_chart_data(code: str, days: int = None) -> pd.DataFrame:
    base_url = f"https://finance.naver.com/item/sise_day.naver?code={code}"
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": f"https://finance.naver.com/item/main.naver?code={code}"
    }

    dfs = []
    pages = 500  # 넉넉하게 확보

    for page in range(1, pages + 1):
        url = f"{base_url}&page={page}"
        res = requests.get(url, headers=headers)
        soup = BeautifulSoup(res.text, "html.parser")
        table = soup.find("table", class_="type2")
        if table:
            try:
                df = pd.read_html(StringIO(str(table)))[0]
                dfs.append(df)
            except Exception:
                continue

    if not dfs:
        raise ValueError("크롤링 실패: 시세 데이터 없음")

    df_all = pd.concat(dfs).dropna()
    df_all.columns = ['날짜', '종가', '전일비', '시가', '고가', '저가', '거래량']
    df_all['날짜'] = pd.to_datetime(df_all['날짜'])
    df_all = df_all.sort_values("날짜")

    # 숫자 변환
    df_all['종가'] = df_all['종가'].astype(str).str.replace(',', '').astype(float)

    # 날짜 요일 붙이기
    weekday_map = {
        'Mon': '월', 'Tue': '화', 'Wed': '수', 'Thu': '목',
        'Fri': '금', 'Sat': '토', 'Sun': '일'
    }
    df_all['날짜'] = df_all['날짜'].apply(
        lambda x: x.strftime('%Y-%m-%d') + f"({weekday_map[x.strftime('%a')]})"
    )

    # days가 주어졌다면 날짜 필터링
    if days:
        today = pd.Timestamp.today().normalize()
        start_date = today - pd.Timedelta(days=days)
        df_all = df_all[df_all['날짜'].apply(lambda x: pd.to_datetime(x[:10])) >= start_date]

    return df_all.reset_index(drop=True)
