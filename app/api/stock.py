from fastapi import APIRouter
from pydantic import BaseModel
from app.nlp.gpt_parser import extract_stock_info, extract_price_info
from app.services.stock_service import get_stock_chart, get_price, get_overseas_price

router = APIRouter(prefix="/api/stock", tags=["Stock"])

class TextRequest(BaseModel):
    text: str

class ChartDirectRequest(BaseModel):
    stock_code: str
    period: str
    name: str

@router.post("/price")
def get_price_info(req: TextRequest):
    parsed = extract_price_info(req.text)
    if not parsed:
        return {"error": "GPT 파싱 실패"}

    code = parsed.get("code")
    intent = parsed.get("intent")
    market = parsed.get("market", "KR") 

    if market == "KR":
        code = code.split(".")[0]  
        return get_price(code, intent)

    elif market == "US":
        if intent == "current_price":
            return get_overseas_price(code)
        else:
            return {"error": "해외 종목은 현재가만 지원합니다."}

    else:
        return {"error": f"Unsupported market type: {market}"}

@router.post("/chart")
def get_chart(req: TextRequest):
    parsed = extract_stock_info(req.text)

    if not parsed or "stock_code" not in parsed:
        return {"error": "GPT 파싱 실패"}

    stock_code = parsed["stock_code"]
    period = parsed["period"]
    name = parsed["name"]

    data = get_stock_chart(stock_code, period)

    return {
        "meta": {
            "name": name,
            "code": stock_code,
            "market": "US" if ".KS" not in stock_code and ".KQ" not in stock_code else "KR",
            "intent": "chart",
            "period": period
        },
        "data": data
    }

# 음성이 아닌 버튼으로 차트를 조회할때
@router.post("/chart/direct")
def get_chart_direct(req: ChartDirectRequest):
    stock_code = req.stock_code
    period = req.period
    name = req.name

    if not stock_code or not period:
        return {"error": "필수값 누락"}

    data = get_stock_chart(stock_code, period)

    return {
        "meta": {
            "name": name,
            "code": stock_code,
            "market": "US" if ".KS" not in stock_code and ".KQ" not in stock_code else "KR",
            "intent": "chart",
            "period": period
        },
        "data": data
    }
