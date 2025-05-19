import yfinance as yf
import pandas as pd
import datetime


# Date: 특정 기간의 각 거래일을 나타내는 지수입니다.
# Open: 특정 날짜에 시장이 개장했을 때 주식이 거래되기 시작한 가격입니다.
# High: 거래일 동안 주식이 도달한 최고 가격입니다.
# Low: 거래일 동안 주식이 도달한 최저 가격입니다.
# Close: 당일 시장이 마감되었을 때 주식이 거래된 최종 가격입니다.
# Adj Close: 배당금, 주식 분할 및 기타 기업 활동에 맞게 조정된 마감 가격으로, 시간이 지남에 따라 주식 가치를 더욱 정확하게 반영합니다.
# Volume: 해당 거래일에 거래된 주식 수입니다.

headers = {
        "User-Agent": "Mozilla/5.0"  # Yahoo 서버가 크롤러를 막지 않게 설정
    }

ticker= yf.Ticker("AAPL")
hist = ticker.history(period="max", interval='1d')
print(hist)
# df = yf.download("AAPL", start='2024-01-01', end='2024-11-05')
# df.to_excel("./AAPL.xlsx")


