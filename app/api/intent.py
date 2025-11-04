from fastapi import APIRouter
from pydantic import BaseModel
from app.nlp.gpt_parser import extract_intent
from app.errors import StockAPIException

router = APIRouter(prefix="/api/intent", tags=["Intent"])

class TextRequest(BaseModel):
    text: str

@router.post("/")
def parse_intent(req: TextRequest):
    parsed = extract_intent(req.text)

    if not parsed:
        raise StockAPIException(status_code=400, detail="GPT 파싱 실패 또는 알 수 없는 요청")

    intent = parsed.get("intent")

    if not intent:
        raise StockAPIException(status_code=400, detail="intent를 추출하지 못했습니다.")

    if intent == "chart":
        code = parsed.get("code")
        name = parsed.get("name")
        market = parsed.get("market", "KR")
        period = parsed.get("period", "3mo")
        return {
            "name": name,
            "code": code,
            "market": market,
            "intent": "chart",
            "period": period,
            "path": f"/api/stock/chart?code={code}&period={period}&market={market}"
        }
    
    elif intent == "realtime_chart":
        code = parsed.get("code")
        name = parsed.get("name")
        market = parsed.get("market", "KR")
        return {
            "name": name,
            "code": code,
            "market": market,
            "intent": "current_price",
            "path": f"/api/stock/ws/trade-price"
        }

    elif intent == "indicator":
        code = parsed.get("code")
        name = parsed.get("name")
        market = parsed.get("market", "KR")
        indicator_type = parsed.get("indicator_type")
        path = f"/api/indicator?code={code}&market={market}"
        if indicator_type:
            path += f"&intent={indicator_type}"
        return {
            "name": name,
            "code": code,
            "market": market,
            "intent": "indicator",
            "indicator_type": indicator_type,
            "path": path
        }

    elif intent == "exchange_rate":
        country = parsed.get("country")
        if not country:
            raise StockAPIException(status_code=400, detail="국가 이름이 필요합니다.")
        # 참고: investment API는 파라미터 이름으로 'contry'를 사용합니다.
        return {
            "intent": "exchange_rate",
            "country": country,
            "path": f"/api/investment/exchange?contry={country}"
        }

    elif intent == "market_index":
        market_name = parsed.get("market_name")
        if not market_name:
            raise StockAPIException(status_code=400, detail="시장 이름이 필요합니다. (예: 코스피, 나스닥)")
        return {
            "intent": "market_index",
            "market_name": market_name,
            "path": f"/api/investment/indices?market={market_name}"
        }

    elif intent in ["current_price", "high_limit", "low_limit"]:
        code = parsed.get("code")
        name = parsed.get("name")
        market = parsed.get("market", "KR")
        return {
            "name": name,
            "code": code,
            "market": market,
            "intent": intent,
            "path": f"/api/stock/price?code={code}&intent={intent}&market={market}"
        }

    raise StockAPIException(status_code=400, detail=f"지원하지 않는 intent입니다: {intent}")