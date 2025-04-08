import requests
import pprint
import json
import pandas as pd
import matplotlib.pyplot as plt


def showChart(data):
    # 응답 JSON 구조에 따라 접근
    items = data['response']['body']['items']['item']

    # DataFrame으로 변환
    df = pd.DataFrame(items)
    df['basDt'] = pd.to_datetime(df['basDt'])  # 날짜 형식으로 변환
    df['clpr'] = pd.to_numeric(df['clpr'])  # 종가 숫자형으로 변환

    # 날짜 순 정렬 (보통 최신이 위에 있음)
    df = df.sort_values('basDt')

    # 그래프 그리기
    plt.figure(figsize=(12, 6))
    plt.plot(df['basDt'], df['clpr'], label='Close Price', color='blue')
    plt.xlabel('Date')
    plt.ylabel('Price (KRW)')
    plt.title('')
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.show()

def printData(data):
    if response.status_code == 200:
        try:
            js = response.json()
            items = js["response"]["body"]["items"]["item"]
            for i in range(1000):
                print(items[i]["basDt"], items[i]["clpr"])
        except Exception as e:
            print("JSON 처리 중 오류:", e)
    else:
        print("API 요청 실패")


endPoint = "https://apis.data.go.kr/1160100/service/GetStockSecuritiesInfoService/getStockPriceInfo"

params = {
    'serviceKey': '여기에 발급받은 서비스 키',
    'numOfRows': 1000, # 한 페이지 결과 수
    'pageNo': 1, # 페이지 번호
    'resultType': 'json', # 구분(xml, json) Default: xml
    'itmsNm': '삼성전자' # 검색값과 종목명이 일치하는 데이터를 검색
}

response = requests.get(endPoint, params=params)
data = response.json()

# printData(data)
showChart(data)




