from fastapi import FastAPI
from app.api import stock, whisper, indicator

app = FastAPI()

# 각 router 등록
app.include_router(whisper.router)
app.include_router(stock.router)