from fastapi import APIRouter, Query
from pydantic import BaseModel
from app.services.stock_service import get_stock_chart, get_price, get_overseas_price

router = APIRouter(prefix="/api/stock", tags=["Stock"])

class ChartDirectRequest(BaseModel):
    stock_code: str
    period: str
    market: str = "KR"

def infer_market(code: str) -> str:
    return "KR" if code.endswith(".KS") or code.endswith(".KQ") else "US"

def validate_market_match(code: str, market: str) -> bool:
    if market == "KR" and not (code.endswith(".KS") or code.endswith(".KQ")):
        return False
    if market == "US" and (code.endswith(".KS") or code.endswith(".KQ")):
        return False
    return True

@router.get("/price")
def get_price_info(
    code: str = Query(..., description="종목 코드 (예: 005930, TSLA 등)"),
    intent: str = Query(..., description="의도 (예: current_price, high_limit, low_limit 등)"),
    market: str = Query("KR", description="시장 구분 (KR | US)")
):
    if market == "KR":
        code = code.split(".")[0]
        return get_price(code, intent)
    elif market == "US":
        if intent == "current_price":
            return get_overseas_price(code)
        return {"error": "해외 종목은 현재가만 지원합니다."}
    return {"error": f"Unsupported market type: {market}"}

@router.get("/chart")
def get_chart_by_query(
    code: str = Query(..., description="야후 파이낸스 형식의 종목 코드 (예: 005930.KS, TSLA)"),
    period: str = Query(..., description="차트 기간 (예: 3mo, 1y 등)"),
    market: str = Query(None, description="시장 구분 (KR | US), 생략 시 자동 추론")
):
    final_market = market or infer_market(code)

    # 유효성 검사
    if not validate_market_match(code, final_market):
        return {"error": f"종목 코드 '{code}'와 시장 '{final_market}'이(가) 일치하지 않습니다."}

    return get_stock_chart(code, period, final_market)

@router.post("/chart/direct")
def get_chart_direct(req: ChartDirectRequest):
    if not req.stock_code or not req.period:
        return {"error": "필수값 누락"}

    # 유효성 검사
    if not validate_market_match(req.stock_code, req.market):
        return {"error": f"종목 코드 '{req.stock_code}'와 시장 '{req.market}'이(가) 일치하지 않습니다."}

    return get_stock_chart(req.stock_code, req.period, req.market)

