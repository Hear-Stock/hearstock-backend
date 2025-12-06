from locust import HttpUser, task, between
from app.data.getCodes import getKospiCodes
import random

class StockApiUser(HttpUser):
    wait_time = between(1, 2)

    def on_start(self):
        codes_dict = getKospiCodes("app/data/kospi100.csv")
        self.codes = [f"{code}.KS" for code in codes_dict.keys()]
        self.countries = ["미국", "일본", "중국", "유럽연합"]
        
        if not self.codes:
            print("Error: 종목 코드를 불러오지 못했습니다. 경로를 확인하세요.")
            self.stop()

    @task(5)
    def get_current_price(self):
        code = random.choice(self.codes).split('.')[0]
        self.client.get(
            "/api/stock/price",
            params={"code": code, "intent": "current_price", "market": "KR"},
            name="/api/stock/price?intent=current_price"
        )

    @task(3)
    def get_3month_chart(self):
        code = random.choice(self.codes)
        self.client.get(
            "/api/stock/chart",
            params={"code": code, "period": "3mo", "market": "KR"},
            name="/api/stock/chart?period=3mo"
        )

    @task(1)
    def get_1year_chart(self):
        code = random.choice(self.codes)
        self.client.get(
            "/api/stock/chart",
            params={"code": code, "period": "1y", "market": "KR"},
            name="/api/stock/chart?period=1y"
        )

    @task(2)
    def get_market_indices(self):
        market = random.choice(["kospi", "kosdaq"])
        self.client.get(
            "/api/investment/indices",
            params={"market": market},
            name="/api/investment/indices"
        )

    @task(1)
    def get_exchange_rate(self):
        country = random.choice(self.countries)
        self.client.get(
            "/api/investment/exchange",
            params={"contry": country},
            name="/api/investment/exchange"
        )

    @task(3)
    def get_all_indicators(self):
        code = random.choice(self.codes).split('.')[0]
        self.client.get(
            "/api/indicator/",
            params={"code": code, "market": "KR"},
            name="/api/indicator/"
        )

    
    