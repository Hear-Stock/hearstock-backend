# from fastapi import APIRouter
# from app.services.stock_service import fetch_price

# router = APIRouter(prefix='/api/stocks', tags=['Stocks'])

# @router.get('/price/{symbol}')
# async def get_stock_price(symbol: str):
#     return await fetch_price(symbol)