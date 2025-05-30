from fastapi import APIRouter
from pydantic import BaseModel
from app.nlp.gpt_parser import extract_intent

router = APIRouter(prefix="/api/intent", tags=["Intent"])

class TextRequest(BaseModel):
    text: str

@router.post("/")
def parse_intent(req: TextRequest):
    parsed = extract_intent(req.text)

    if not parsed:
        return {"error": "GPT 파싱 실패 또는 알 수 없는 요청"}

    intent = parsed["intent"]
    code = parsed["code"]
    name = parsed["name"]
    market = parsed.get("market", "KR")

    if intent == "chart":
        period = parsed.get("period", "3mo")  # 기본값 지정 가능
        return {
            "name": name,
            "code": code,
            "market": market,
            "intent": "chart",
            "period": period,
            "path": f"/api/stock/chart?code={code}&period={period}"
        }

    elif intent == "indicator":
        return {
            "name": name,
            "code": code,
            "market": market,
            "intent": "indicator",
            "path": "/api/indicator"
        }

    elif intent in ["current_price", "high_limit", "low_limit"]:
        return {
            "name": name,
            "code": code,
            "market": market,
            "intent": intent,
            "path": "/api/stock/price"
        }

    return {"error": f"지원하지 않는 intent입니다: {intent}"}
