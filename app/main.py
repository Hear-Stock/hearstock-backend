from fastapi import FastAPI
from app.api import stock, stock_cur, indicator, intent

app = FastAPI()

# 각 router 등록
app.include_router(stock.router)
app.include_router(intent.router)
app.include_router(indicator.router)
app.include_router(stock_cur.router)