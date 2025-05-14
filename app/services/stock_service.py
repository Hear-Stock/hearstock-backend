import requests
import redis
import json
from bs4 import BeautifulSoup
import yfinance as yf
import os
from dotenv import load_dotenv

load_dotenv()
REDIS_HOST = os.getenv("REDIS_HOST")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_DB = int(os.getenv("REDIS_DB", 0))

r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, decode_responses=True)
print("Redis host:", REDIS_HOST)  # localhost가 출력돼야 함


# 해외 현재가 조회
def get_overseas_price(symbol: str):
    import yfinance as yf
    ticker = yf.Ticker(symbol)
    data = ticker.history(period="1d", interval="1m")

    if data.empty:
        return {"error": f"No data for {symbol}"}

    return {
        "code": symbol,
        "current_price": round(data["Close"].iloc[-1], 2)
    }

# 국내 상한가, 하한가, 현재가 조회
def get_domestic_price(code: str) -> dict:
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

# 주가, 상한가, 하한가 조회
def get_price(code: str, intent: str) -> dict:
    summary = get_domestic_price(code)
    
    if "error" in summary:
        return summary

    name = summary.get("name")

    if intent == "current_price":
        return {"name": name, "current_price": summary.get("current")}
    elif intent == "high_limit":
        return {"name": name, "high_limit": summary.get("high_limit")}
    elif intent == "low_limit":
        return {"name": name, "low_limit": summary.get("low_limit")}
    else:
        return {"error": f"지원하지 않는 intent: {intent}"}
    
def get_stock_chart(stock_code: str, period: str):
    cache_key = f"chart:{stock_code}:{period}"
    
    cached_data = r.get(cache_key)

    try:
        ticker = yf.Ticker(stock_code)
        _ = ticker.info
        df = ticker.history(period=period, interval="1d")
    except Exception as e:
        return {"error": f"yfinance error: {e}"}

    if df.empty:
        return {"error": "No chart data available."}

    df = df.reset_index()
    df["date"] = df["Date"].dt.strftime("%Y-%m-%d")
    df = df[["date", "Open", "High", "Low", "Close", "Volume"]]

    df.rename(columns={
        "Open": "open",
        "High": "high",
        "Low": "low",
        "Close": "close",
        "Volume": "volume"
    }, inplace=True)

    df["fluctuation_rate"] = df["close"].pct_change() * 100
    df["fluctuation_rate"] = df["fluctuation_rate"].round(2)
    df = df.dropna()

    result = df.to_dict(orient="records")

    r.setex(cache_key, 3600, json.dumps(result))

    return result

