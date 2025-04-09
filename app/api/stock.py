from fastapi import APIRouter, Query
from app.services.stock_service import get_current_price, get_price_summary, get_chart_data

router = APIRouter(prefix="/api/stock", tags=["Stock"])

@router.get("/summary/{code}")
def get_summary(code: str):
    return get_price_summary(code)

@router.get("/{code}")
def get_price(code: str):
    price = get_current_price(code)
    return {"code": code, "price": price}

@router.get("/chart/{code}")
def chart_data(code: str, days: int = Query(60, ge=7, le=1825)):
    df = get_chart_data(code, days)
    return df.to_dict(orient="records")