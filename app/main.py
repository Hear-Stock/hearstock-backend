from fastapi import FastAPI
from app.api import stock, indicator, investment, intent, naverNews

app = FastAPI()

# 각 router 등록
app.include_router(stock.router)
app.include_router(intent.router)
app.include_router(indicator.router)
app.include_router(investment.router)
app.include_router(naverNews.router)