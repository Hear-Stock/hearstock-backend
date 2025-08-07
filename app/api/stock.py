from fastapi import APIRouter, Query, Response
from pydantic import BaseModel
import os
import subprocess
import uuid
import json
from app.services.stock_service import get_stock_chart, get_price, get_overseas_price
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

# @router.get("/generate-audio")
# def generate_audio_by_stock(
#     code: str = Query(..., description="야후 파이낸스 형식의 종목 코드 (예: 005930.KS, TSLA)"),
#     period: str = Query("1mo", description="차트 기간 (예: 1mo, 3mo 등)"),
#     market: str = Query(None, description="시장 구분 (KR | US), 생략 시 자동 추론")
# ):
#     # 시장 추론
#     final_market = market or infer_market(code)

#     # 유효성 검사
#     if not validate_market_match(code, final_market):
#         return Response(content="시장/코드 불일치", status_code=400)

#     # 차트 데이터 가져오기
#     chart_data = get_stock_chart(code, period, final_market)
#     if not chart_data or len(chart_data) == 0:
#         return Response(content="차트 데이터 없음", status_code=404)

#     # 고유 파일 이름 생성
#     uid = uuid.uuid4().hex
#     json_file = f"stock_data_{uid}.json"
#     wav_file = f"output_{uid}.wav"

#     # JSON 파일로 저장
#     with open(json_file, "w") as f:
#         json.dump(chart_data, f)

#     # C++ 실행
#     result = subprocess.run(["./hrtf_converter", json_file, wav_file])

#     # 실패 시
#     if result.returncode != 0 or not os.path.exists(wav_file):
#         return Response(content="HRTF 변환 실패", status_code=500)

#     # WAV 반환
#     with open(wav_file, "rb") as f:
#         audio_bytes = f.read()

#     # 임시 파일 삭제
#     os.remove(json_file)
#     os.remove(wav_file)

#     return Response(content=audio_bytes, media_type="audio/wav")

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

