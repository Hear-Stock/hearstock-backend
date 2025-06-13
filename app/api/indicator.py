from fastapi import APIRouter, Query
from app.services.indicator_service import get_investment_metrics

router = APIRouter(prefix="/api/indicator", tags=["Indicator"])

# 투자지표 조회 (쿼리 기반)
@router.get("/")
def get_investment_info(
    code: str = Query(..., description="종목 코드 (예: 005930, TSLA 등)"),
    market: str = Query("KR", description="시장 구분 (KR | US)")
):
    data = get_investment_metrics(code, market)
    if "error" in data:
        return {"error": data["error"]}
    return data

# 특정 지표 설명 조회 (쿼리 기반)
@router.get("/explain")
def explain_metric(
    code: str = Query(..., description="종목 코드"),
    market: str = Query("KR", description="시장"),
    metric: str = Query(..., description="지표명 (예: PER, PBR, ROE 등)")
):
    data = get_investment_metrics(code, market)

    if "error" in data:
        return {"text": f"해당 종목의 투자지표를 불러올 수 없습니다. ({data['error']})"}

    value = data.get(metric)
    industry_per = data.get("industry_per")
    industry_rate = data.get("industry_rate")

    if value is None:
        return {"text": f"{metric} 지표는 제공되지 않습니다."}

    # 요약에서 해당 metric 관련 문장 추출
    if industry_per:
        return {"text": f"{metric}은 {value}이며, 현재 산업 평균 PER은 {industry_per}, 등락률은 {industry_rate} 입니다."}

    return {
        "text": f"{metric} 값은 {value}입니다. 현재 산업 평균과의 비교 정보는 제공되지 않습니다."
    }
