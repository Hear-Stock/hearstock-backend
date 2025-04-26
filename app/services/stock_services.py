import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime, timedelta
import psycopg2
import time

def fetch_minute_data(stock_code, date):
    """
    특정 날짜의 분봉 데이터를 네이버에서 크롤링
    """
    base_url = f"https://finance.naver.com/item/sise_time.naver?code={stock_code}"
    headers = {"User-Agent": "Mozilla/5.0"}
    target_time = f"{date.strftime('%Y%m%d')}153000"  # 장 마감 기준
    page = 1
    records = []

    while True:
        url = f"{base_url}&thistime={target_time}&page={page}"
        res = requests.get(url, headers=headers)
        res.encoding = 'euc-kr'
        soup = BeautifulSoup(res.text, 'html.parser')
        rows = soup.select("table.type2 tr")

        before_count = len(records)

        for row in rows:
            cols = row.select("td")
            if len(cols) == 6:
                try:
                    time_str = cols[0].text.strip()
                    price = int(cols[1].text.strip().replace(',', ''))
                    volume = int(cols[5].text.strip().replace(',', ''))

                    full_datetime = datetime.strptime(
                        f"{date.strftime('%Y-%m-%d')} {time_str}", "%Y-%m-%d %H:%M"
                    )

                    records.append({"datetime": full_datetime, "price": price, "volume": volume})
                except:
                    continue

        if len(records) == before_count:
            break

        page += 1
        time.sleep(0.3)  # 서버 부하 방지

    return pd.DataFrame(records)


def resample_to_10min(df):
    """
    1분 체결 데이터를 10분 봉으로 리샘플링
    """
    df = df.set_index("datetime").sort_index()
    ohlc = df["price"].resample("10T").ohlc()
    vol = df["volume"].resample("10T").sum()
    result = ohlc.join(vol)
    result.columns = ["open", "high", "low", "close", "volume"]
    result.dropna(inplace=True)

    # 등락률 계산
    prev_close = None
    result["change_rate"] = 0.0
    for idx, row in result.iterrows():
        if prev_close:
            change = (row["close"] - prev_close) / prev_close * 100
            result.at[idx, "change_rate"] = round(change, 2)
        prev_close = row["close"]

    return result


def insert_to_postgresql(df, stock_code):
    conn = psycopg2.connect(
        dbname="stockdb",
        user="stockuser",
        password="stockpass",
        host="localhost",
        port="5432"
    )
    cur = conn.cursor()

    for idx, row in df.iterrows():
        sql = """
        INSERT INTO stock_10min (stock_code, timestamp, open, high, low, close, volume, change_rate)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (stock_code, timestamp) DO NOTHING;
        """
        cur.execute(sql, (
            stock_code,
            idx,
            row["open"],
            row["high"],
            row["low"],
            row["close"],
            int(row["volume"]),
            float(row["change_rate"])
        ))

    conn.commit()
    cur.close()
    conn.close()


def crawl_and_store(stock_code, start_date, end_date):
    """
    여러 날짜에 대해 반복 수집
    """
    curr = start_date
    while curr <= end_date:
        print(f"📅 {curr.strftime('%Y-%m-%d')} 크롤링 중...")
        df = fetch_minute_data(stock_code, curr)
        if df.empty:
            print(f"⚠️ 데이터 없음: {curr.strftime('%Y-%m-%d')}")
        else:
            df10 = resample_to_10min(df)
            insert_to_postgresql(df10, stock_code)
            print(f"✅ {curr.strftime('%Y-%m-%d')} 저장 완료 ({len(df10)}개)")
        curr += timedelta(days=1)
        time.sleep(1)

# 실행 예시
crawl_and_store("005930", datetime(2025, 4, 11), datetime(2025, 4, 18))
