from locust import HttpUser, task, between
from app.data.getCodes import getKospiCodes
import random

class StockApiUser(HttpUser):
    wait_time = between(1, 2)  # 요청 간 대기 시간 (1~2초)


    kospi_codes = getKospiCodes("app/data/kospi100.csv")
    codes = list(kospi_codes.keys())
    # codes = ["005930", "000660", "207940"]

    @task(0)
    def get_stock_chart(self):
        code = random.choice(self.codes)
        
        
        # GET 요청 보내기
        self.client.get(
            "/api/stk/stkchart",
            params={"code": code}
        )

    @task
    def get_stock_chart_nocache(self):
        code = random.choice(self.codes)
        
        # GET 요청 보내기
        self.client.get(
            "/api/stk/kiwoomStockChart",
            params={"code": code}
        )

    
    