import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import datetime

tsla= yf.Ticker("005930.KS")

# Date: 특정 기간의 각 거래일을 나타내는 지수입니다.
# Open: 특정 날짜에 시장이 개장했을 때 주식이 거래되기 시작한 가격입니다.
# High: 거래일 동안 주식이 도달한 최고 가격입니다.
# Low: 거래일 동안 주식이 도달한 최저 가격입니다.
# Close: 당일 시장이 마감되었을 때 주식이 거래된 최종 가격입니다.
# Adj Close: 배당금, 주식 분할 및 기타 기업 활동에 맞게 조정된 마감 가격으로, 시간이 지남에 따라 주식 가치를 더욱 정확하게 반영합니다.
# Volume: 해당 거래일에 거래된 주식 수입니다.

# 최근 데이터 가져오기
# hist = tsla.history(period="1d")
# print(hist)


startDate = datetime.datetime(2015, 4, 8)
endDate = datetime.datetime(2025, 4, 8)
stock_data = yf.Ticker('005930.KS')
stock_df = stock_data.history(start=startDate, end=endDate)
stock_df['Close'].plot(title="005930.KS stock")
# plt.show()  
plt.savefig("plot.png")
