import pandas as pd
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import psycopg2
import time

def get_pg_connection():
    return psycopg2.connect(
        dbname="hear_stock",
        user="postgres",
        password="postgres",
        host="localhost",
        port="5432"
    )


def load_stock_codes(file_path: str) -> list[str]:
    df = pd.read_csv(file_path, encoding='cp949')
    return df['종목코드'].astype(str).tolist()


def fetch_minute_data(stock_code: str, date: datetime) -> pd.DataFrame:
    base_url = f"https://finance.naver.com/item/sise_time.naver?code={stock_code}"
    headers = {"User-Agent": "Mozilla/5.0"}
    target_time = f"{date.strftime('%Y%m%d')}153000"
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

                    records.append({
                        "datetime": full_datetime,
                        "price": price,
                        "volume": volume
                    })
                except:
                    continue

        if len(records) == before_count:
            break

        page += 1
        time.sleep(0.3)

    return pd.DataFrame(records)


def resample_to_10min(df):
    df = df.set_index("datetime").sort_index()
    ohlc = df["price"].resample("10T").ohlc()
    vol = df["volume"].resample("10T").sum()
    result = ohlc.join(vol)
    result.columns = ["open", "high", "low", "close", "volume"]
    result.dropna(inplace=True)

    # 등락률 계산
    result["change_rate"] = 0.0
    prev_close = None
    for idx, row in result.iterrows():
        if prev_close:
            change = (row["close"] - prev_close) / prev_close * 100
            result.at[idx, "change_rate"] = round(change, 2)
        prev_close = row["close"]

    return result


def insert_to_postgresql(df, stock_code):
    conn = get_pg_connection()
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


def crawl_all_stocks(stock_list_path: str, start_date: str, end_date: str):
    stock_codes = load_stock_codes(stock_list_path)
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")

    for code in stock_codes:
        curr = start
        print(f"\n📈 종목 시작: {code}")
        while curr <= end:
            try:
                print(f"  📅 {curr.strftime('%Y-%m-%d')} 수집 중...")
                df = fetch_minute_data(code, curr)
                if not df.empty:
                    df10 = resample_to_10min(df)
                    insert_to_postgresql(df10, code)
                    print(f"    ✅ 저장 완료 ({len(df10)}개)")
                else:
                    print(f"    ⚠️ 데이터 없음")
            except Exception as e:
                print(f"    ❌ 실패: {e}")
            curr += timedelta(days=1)
            time.sleep(1)

# ✅ 실행
if __name__ == "__main__":
    crawl_all_stocks("stock_list.csv", "2025-04-11", "2025-04-18")