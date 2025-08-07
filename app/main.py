from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import stock, indicator, investment, intent, naverNews

app = FastAPI()

origins = [
    "http://localhost:7789",
    "http://localhost:3000"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"]
)

# 각 router 등록
app.include_router(stock.router)
app.include_router(intent.router)
app.include_router(indicator.router)
app.include_router(investment.router)
app.include_router(naverNews.router)