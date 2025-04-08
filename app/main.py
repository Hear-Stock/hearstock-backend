from fastapi import FastAPI
from app.api import stocks, whisper, indicators

app = FastAPI()

# 각 router 등록
app.include_router(whisper.router)
#app.include_router(stocks.router)
#app.include_router(indicators.router)