import requests
from curl_cffi import requests
import redis
import json
from bs4 import BeautifulSoup
import yfinance as yf
import os
from dotenv import load_dotenv
import pandas as pd
from datetime import datetime, date
from .kiwoom_service import fetch_chart_data

load_dotenv()
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_DB = int(os.getenv("REDIS_DB", 0))

r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, decode_responses=True)

# 해외 현재가 조회
def get_overseas_price(symbol: str):
    session = requests.Session(impersonate="chrome")

    ticker = yf.Ticker(symbol, session=session)
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

# 환율 변환 함수   
def get_usd_to_krw_rate():
    try:
        res = requests.get("https://finance.naver.com/marketindex/exchangeDetail.naver?marketindexCd=FX_USDKRW")
        res.encoding = "utf-8"
        rate_text = res.text.split("blind\">")[1].split("</span>")[0].replace(",", "")
        return float(rate_text)
    except:
        return 1350.0
        
def get_stock_chart(stock_code: str, period: str, market: str = None):
    cache_key = f"chart:{stock_code}:{period}:{market}"

    cached = r.get(cache_key)
    if cached:
        try:
            return json.loads(cached)
        except json.JSONDecodeError:
            pass  

    result = []

    if market == "KR":
        code = stock_code.split(".")[0]

        df = fetch_chart_data(code=code, period=period)

        if isinstance(df, dict) and "error" in df:
            return df

        df = pd.DataFrame(df)  
        df = df.replace([float('inf'), float('-inf')], pd.NA).fillna(0) # 결측치 처리

        result = df.to_dict(orient="records")

    elif market == "US":
        try:
            period_map = {
                "1mo": "1d",
                "3mo": "1d",
                "1y": "1wk",
                "5y": "1mo",
                "10y": "1mo",
                "all": "1mo"
            }

            if period not in period_map:
                return {"error": f"지원하지 않는 기간: {period}"}

            interval = period_map[period]

            session = requests.Session(impersonate="chrome")
            ticker = yf.Ticker(stock_code, session=session)
            df = ticker.history(period=period if period != "all" else "max", interval=interval)

            if df.empty:
                return {"error": "No chart data available."}

            df = df.reset_index()
            df["timestamp"] = df["Date"].dt.strftime("%Y-%m-%d")
            df = df[["timestamp", "Open", "High", "Low", "Close", "Volume"]]

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

            usd_to_krw = get_usd_to_krw_rate()

            for row in df.to_dict(orient="records"):
                item = dict(row)
                item["open"] = round(item["open"], 2)
                item["high"] = round(item["high"], 2)
                item["low"] = round(item["low"], 2)
                item["close"] = round(item["close"], 2)

                item["open_krw"] = int(item["open"] * usd_to_krw)
                item["high_krw"] = int(item["high"] * usd_to_krw)
                item["low_krw"] = int(item["low"] * usd_to_krw)
                item["close_krw"] = int(item["close"] * usd_to_krw)

                result.append(item)

        except Exception as e:
            return {"error": f"yfinance error: {e}"}

    else:
        return {"error": f"지원하지 않는 market: {market}"}

    r.setex(cache_key, 3600, json.dumps(result))
    return result

def get_stock_chart_range(stock_code: str, start: date, end: date, market: str = None):
    cache_key = f"chart_range:{stock_code}:{start}:{end}:{market}"

    # Redis 캐시 확인
    cached = r.get(cache_key)
    if cached:
        try:
            return json.loads(cached)
        except json.JSONDecodeError:
            pass

    # 3개월치 데이터를 가져와서 필터링 (이미 캐시되어 있을 가능성 높음)
    full_data = get_stock_chart(stock_code, "3mo", market)

    # 에러가 반환된 경우 그대로 전달
    if isinstance(full_data, dict) and "error" in full_data:
        return full_data

    # 날짜 필터링
    filtered = [
        item for item in full_data
        if start <= datetime.strptime(item["timestamp"], "%Y-%m-%d").date() <= end
    ]

    # Redis에 캐싱 (1시간 TTL)
    r.setex(cache_key, 3600, json.dumps(filtered))

    return filtered