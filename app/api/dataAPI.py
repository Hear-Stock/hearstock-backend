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
    'serviceKey': '79q0SKoHP/mpdu8C5Z1Ox9TMHKcPf8+suloysjNhmPmCamXI1eunTRfE/NxNPomTgvCIguz+05jk3s43Qg71nA==',  # 인증용 서비스 키
    'numOfRows': 1000,  # 한 페이지에 가져올 결과 수
    'pageNo': 1,  # 페이지 번호
    'resultType': 'json',  # 응답 형식 (xml 또는 json, 기본값 xml)

    'basDt': '',  # 기준일자 (예: 20220919) - 정확히 일치하는 데이터 검색
    'beginBasDt': '',  # 기준일자가 지정값보다 크거나 같은 데이터 검색
    'endBasDt': '',  # 기준일자가 지정값보다 작은 데이터 검색
    'likeBasDt': '',  # 기준일자값이 포함된 데이터 검색

    'likeSrtnCd': '',  # 단축코드 포함 검색
    'isinCd': '',  # ISIN 코드가 정확히 일치하는 데이터 검색
    'likeIsinCd': '',  # ISIN 코드가 포함된 데이터 검색

    'itmsNm': '삼성전자',  # 종목명이 정확히 일치하는 데이터 검색
    'likeItmsNm': '',  # 종목명이 포함된 데이터 검색

    'mrktCls': '',  # 시장구분 (예: KOSDAQ, KOSPI)

    'beginVs': '',  # 대비가 지정값보다 크거나 같은 데이터 검색
    'endVs': '',  # 대비가 지정값보다 작은 데이터 검색

    'beginFltRt': '',  # 등락률이 지정값보다 크거나 같은 데이터 검색
    'endFltRt': '',  # 등락률이 지정값보다 작은 데이터 검색

    'beginTrqu': '',  # 거래량이 지정값보다 크거나 같은 데이터 검색
    'endTrqu': '',  # 거래량이 지정값보다 작은 데이터 검색

    'beginTrPrc': '',  # 거래대금이 지정값보다 크거나 같은 데이터 검색
    'endTrPrc': '',  # 거래대금이 지정값보다 작은 데이터 검색

    'beginLstgStCnt': '',  # 상장주식수가 지정값보다 크거나 같은 데이터 검색
    'endLstgStCnt': '',  # 상장주식수가 지정값보다 작은 데이터 검색

    'beginMrktTotAmt': '',  # 시가총액이 지정값보다 크거나 같은 데이터 검색
    'endMrktTotAmt': '',  # 시가총액이 지정값보다 작은 데이터 검색
    'serviceKey': '여기에 발급받은 서비스 키',
    'numOfRows': 1000, # 한 페이지 결과 수
    'pageNo': 1, # 페이지 번호
    'resultType': 'json', # 구분(xml, json) Default: xml
    'itmsNm': '삼성전자' # 검색값과 종목명이 일치하는 데이터를 검색
}


response = requests.get(endPoint, params=params)
data = response.json()

printData(data)
showChart(data)




