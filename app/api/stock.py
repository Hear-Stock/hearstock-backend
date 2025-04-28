from fastapi import APIRouter, Query
from app.services.stock_service import get_daily_stock_data

router = APIRouter(prefix="/api/stock", tags=["Stock"])

@router.get("/chart")
async def get_stock_chart(
    stock_code: str = Query(..., description="주식 종목 코드 (예: 005930)"),
    page: int = Query(1, description="조회할 페이지 번호 (기본값 1)")
):

    data = get_daily_stock_data(stock_code, page)
    return {"stock_code": stock_code, "page": page, "data": data}