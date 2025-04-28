# 실시간 차트 조회 api

import websocket
import threading
import json
import time
import pandas as pd
from app.db.db_service import save_ohlcv
from app.config import APP_KEY, APP_SECRET, STOCK_CODE
from app.services.utils import get_access_token

realtime_data = []

def on_message(ws, message):
    data = json.loads(message)
    body = data.get('body', {})
    output = body.get('output', {})

    realtime_data.append({
        'code': output.get('stck_shrn_iscd'),
        'price': float(output.get('stck_prpr', 0)),
        'high': float(output.get('stck_hgpr', 0)),
        'low': float(output.get('stck_lwpr', 0)),
        'open': float(output.get('stck_oprc', 0)),
        'chg_rate': float(output.get('prdy_ctrt', 0)),
        'volume': int(output.get('acml_vol', 0)),
        'time': output.get('tr_tm')
    })

def on_open(ws):
    token = get_access_token()
    subscribe_message = {
        "header": {
            "authorization": f"Bearer {token}",
            "appkey": APP_KEY,
            "appsecret": APP_SECRET,
            "tr_type": "1",
            "content-type": "utf-8"
        },
        "body": {
            "input": {
                "tr_id": "H0STCNT0",
                "tr_key": STOCK_CODE
            }
        }
    }
    ws.send(json.dumps(subscribe_message))

def start_websocket():
    ws = websocket.WebSocketApp(
        "wss://ops.koreainvestment.com:9443/ws",
        on_open=on_open,
        on_message=on_message
    )
    threading.Thread(target=ws.run_forever, daemon=True).start()

def start_scheduler():
    while True:
        time.sleep(600)  # 10분
        if realtime_data:
            df = pd.DataFrame(realtime_data)
            df['datetime'] = pd.to_datetime(df['time'], format='%H%M%S')
            df.set_index('datetime', inplace=True)

            ohlcv = {
                'code': df['code'].iloc[0],
                'open': df['open'].iloc[0],
                'close': df['price'].iloc[-1],
                'high': df['high'].max(),
                'low': df['low'].min(),
                'chg_rate': df['chg_rate'].iloc[-1],
                'volume': df['volume'].diff().sum(),
                'timestamp': pd.Timestamp.now().floor('T')
            }

            # save_ohlcv(ohlcv)
            realtime_data.clear()
