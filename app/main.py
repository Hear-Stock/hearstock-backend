from fastapi import FastAPI
from app.api import stock, indicator

app = FastAPI()

# 각 router 등록
app.include_router(stock.router)
app.include_router(indicator.router)