from fastapi import APIRouter, Query, HTTPException
from datetime import datetime
from pydantic import BaseModel
from app.services.stock_service import get_stock_chart, get_price, get_overseas_price, get_stock_chart_range
from app.api.kiwoomREST import get_kiwoom_token,get_stock_code, get_stocks_by_keyword

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

@router.get("/chart/range")
def get_chart_by_range(
    code: str = Query(..., description="야후 파이낸스 형식의 종목 코드 (예: 005930.KS, TSLA)"),
    start: str = Query(..., description="드래그 시작일 (YYYY-MM-DD)"),
    end: str = Query(..., description="드래그 종료일 (YYYY-MM-DD)"),
    market: str = Query(None, description="시장 구분 (KR | US), 생략 시 자동 추론")
):
    final_market = market or infer_market(code)

    if not validate_market_match(code, final_market):
        raise HTTPException(status_code=400, detail=f"종목 코드 '{code}'와 시장 '{final_market}'이(가) 일치하지 않습니다.")

    try:
        start_date = datetime.strptime(start, "%Y-%m-%d").date()
        end_date = datetime.strptime(end, "%Y-%m-%d").date()
        if start_date > end_date:
            raise HTTPException(status_code=400, detail="시작일이 종료일보다 늦습니다.")
    except ValueError:
        raise HTTPException(status_code=400, detail="날짜 형식이 잘못되었습니다 (YYYY-MM-DD)")

    data = get_stock_chart_range(code, start_date, end_date, final_market)

    return {
        "meta": {
            "code": code,
            "period": {"start": start, "end": end},
            "count": len(data)
        },
        "data": data
    }

@router.get("/findcode")
def get_code(company_name: str = Query(..., description="기업 이름 입력 예) 삼성전자, SK하이닉스")
			 ,market: str = Query(..., description="0:코스피, 10: 코스닥")):
	
	result = get_stock_code(token=get_kiwoom_token(), company_name=company_name, market=market)

	return result

@router.get("/findstk")
def get_name_and_code(
		keyword: str = Query(..., description="키워드 입력 예) 삼성, 현대")
		,market: str = Query(..., description="0:코스피, 10: 코스닥") ):
	
	result = get_stocks_by_keyword(token=get_kiwoom_token(), keyword=keyword, market=market)

	return result

