from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.api import stock, whisper, indicator
from app.services.stock_realtime_service import start_websocket, start_scheduler
import threading

@asynccontextmanager
async def lifespan(app: FastAPI):
    start_websocket()
    threading.Thread(target=start_scheduler, daemon=True).start()
    print("🚀 실시간 체결 수집 + 10분 저장 스케줄러 시작 완료")
    yield

app = FastAPI()

# 각 router 등록
app.include_router(whisper.router)
app.include_router(stock.router)
app.include_router(indicator.router)