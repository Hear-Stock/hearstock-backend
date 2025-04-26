from fastapi import APIRouter, HTTPException
from app.services.indicator_service import crawl_investment_metrics
from app.schemas.indicator_schema import InvestmentIndicators

router = APIRouter(prefix="/api/indicator", tags=["Indicator"])

@router.get("/{stock_code}", response_model=InvestmentIndicators)
async def get_investment_indicators(stock_code: str):
    data = crawl_investment_metrics(stock_code)
    if "error" in data:
        raise HTTPException(status_code=500, detail=data["error"])
    return data
