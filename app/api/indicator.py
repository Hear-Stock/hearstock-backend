from fastapi import APIRouter
from pydantic import BaseModel
from app.services.indicator_service import get_investment_metrics
from app.nlp.gpt_parser import extract_price_info

class TextRequest(BaseModel):
    text: str

router = APIRouter(prefix="/api/indicator", tags=["Indicator"])

@router.post("/")
def get_investment_info(req: TextRequest):
    parsed = extract_price_info(req.text)
    if not parsed:
        return {"error": "GPT 파싱 실패"}

    code = parsed.get("code")
    market = parsed.get("market", "KR")

    if not code:
        return {"error": "종목 코드 없음"}

    data = get_investment_metrics(code, market)
    if "error" in data:
        return {"error": data["error"]}

    return {
        "meta": parsed, 
        "data": data    
    }