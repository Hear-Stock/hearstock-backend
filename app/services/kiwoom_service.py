import os
import json
import time
import pandas as pd
from datetime import datetime, timedelta
from dotenv import load_dotenv
import requests

load_dotenv()

API_KEY = os.getenv("KIWOOM_REST_KEY")
SECRET_KEY = os.getenv("KIWOOM_REST_SECRET")

# 토큰 발급 함수
def get_kiwoom_token():
    host = 'https://mockapi.kiwoom.com'
    endpoint = '/oauth2/token'
    url = host + endpoint

    headers = {
        'Content-Type': 'application/json;charset=UTF-8',
    }

    params = {
        'grant_type': 'client_credentials',
        'appkey': API_KEY,
        'secretkey': SECRET_KEY,
    }

    response = requests.post(url, headers=headers, json=params)
    response.raise_for_status()
    response = response.json()
    return response['token']

def fn_ka10081(token, cont_yn='N', next_key='', code="", date="20250501"):
    host = 'https://mockapi.kiwoom.com'
    endpoint = '/api/dostk/chart'
    url = host + endpoint

    headers = {
        'Content-Type': 'application/json;charset=UTF-8',
        'authorization': f'Bearer {token}',
        'cont-yn': cont_yn,
        'next-key': next_key,
        'api-id': 'ka10081',
    }

    params = {
        'stk_cd': code,
        'base_dt': date,
        'upd_stkpc_tp': '1',
    }

    response = requests.post(url, headers=headers, json=params)
    next_key_val = response.headers.get('next-key')
    data = response.json()
    return pd.DataFrame(data.get('stk_dt_pole_chart_qry', [])), next_key_val

def get_kiwoom_chart(token, code, date=datetime.now().strftime("%Y%m%d")):
    all_data = []
    next_key_val = ""
    while True:
        time.sleep(0.5)
        data, next_key_val = fn_ka10081(token=token, code=code, date=date, cont_yn='Y', next_key=next_key_val)

        if data.empty:
            break
        all_data.append(data)
        if not next_key_val:
            break

    if not all_data:
        return pd.DataFrame()

    all_data = pd.concat(all_data, ignore_index=True)

    # 문자열 → 숫자 변환
    numeric_columns = ['cur_prc', 'trde_qty', 'open_pric', 'high_pric', 'low_pric']
    all_data[numeric_columns] = all_data[numeric_columns].apply(pd.to_numeric, errors='coerce')

    # 날짜 변환
    all_data['dt'] = pd.to_datetime(all_data['dt'], format='%Y%m%d')

    # 컬럼 정리
    df = all_data.rename(columns={
        'cur_prc': 'close',
        'open_pric': 'open',
        'high_pric': 'high',
        'low_pric': 'low',
        'trde_qty': 'volume',
        'dt': 'timestamp'
    })[['timestamp', 'open', 'high', 'low', 'close', 'volume']]

    return df

def fetch_chart_data(code: str, period: str = "3mo"):
    try:
        token = get_kiwoom_token()
        df = get_kiwoom_chart(token=token, code=code)

        if df.empty:
            return {"error": "데이터 없음"}

        # 정렬 (오래된 순)
        df = df.sort_values(by="timestamp", ascending=True)

        # 기간 필터
        end_date = datetime.now()
        start_date = {
            "3mo": end_date - timedelta(days=91),
            "1y": end_date - timedelta(days=365),
            "5y": end_date - timedelta(days=1825),
            "all": datetime.min
        }.get(period, None)

        if start_date is None:
            return {"error": f"지원하지 않는 기간: {period}"}

        df = df[df["timestamp"] >= start_date]

        # 리샘플링
        if period == "1y":
            df = df.set_index("timestamp").resample("7D").agg({
                "open": "first",
                "high": "max",
                "low": "min",
                "close": "last",
                "volume": "sum"
            }).dropna().reset_index()
        elif period in ["5y", "all"]:
            df = df.set_index("timestamp").resample("M").agg({
                "open": "first",
                "high": "max",
                "low": "min",
                "close": "last",
                "volume": "sum"
            }).dropna().reset_index()

        # 등락률 계산
        df["prev_close"] = df["close"].shift(1)
        df["fluctuation_rate"] = ((df["close"] - df["prev_close"]) / df["prev_close"]) * 100
        df["fluctuation_rate"] = df["fluctuation_rate"].round(2)
        df = df.dropna(subset=["fluctuation_rate"])
        df = df.drop(columns=["prev_close"])

        # 날짜 포맷
        df["timestamp"] = df["timestamp"].dt.strftime("%Y-%m-%d")

        df = df[["timestamp", "open", "high", "low", "close", "volume", "fluctuation_rate"]]
        return df.to_dict(orient="records")

    except Exception as e:
        return {"error": f"kiwoom_service error: {str(e)}"}
