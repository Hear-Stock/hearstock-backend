from fastapi import APIRouter, Query, HTTPException, WebSocket, WebSocketDisconnect
from datetime import datetime
from pydantic import BaseModel
import os
import subprocess
import uuid
import json
import asyncio
import websockets
from websockets.protocol import State 
import logging
from app.services.stock_service import get_stock_chart, get_price, get_overseas_price, get_stock_chart_range
from app.api.kiwoomREST import get_kiwoom_token,get_stock_code, get_stocks_by_keyword
from app.errors import StockAPIException
from app.services.kiwoom_connection_manager import KiwoomConnectionManager as connection_manager


ACCESS_TOKEN = get_kiwoom_token()  # 고객 Access Token

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
        raise StockAPIException(status_code=400, detail="해외 종목은 현재가만 지원합니다.")
    raise StockAPIException(status_code=400, detail=f"Unsupported market type: {market}")

@router.get("/chart")
def get_chart_by_query(
    code: str = Query(..., description="야후 파이낸스 형식의 종목 코드 (예: 005930.KS, TSLA)"),
    period: str = Query(..., description="차트 기간 (예: 3mo, 1y 등)"),
    market: str = Query(None, description="시장 구분 (KR | US), 생략 시 자동 추론")
):
    final_market = market or infer_market(code)

    # 유효성 검사
    if not validate_market_match(code, final_market):
        raise StockAPIException(status_code=400, detail=f"종목 코드 '{code}'와 시장 '{final_market}'이(가) 일치하지 않습니다.")

    return get_stock_chart(code, period, final_market)

@router.post("/chart/direct")
def get_chart_direct(req: ChartDirectRequest):
    if not req.stock_code or not req.period:
        raise StockAPIException(status_code=400, detail="필수값 누락")

    # 유효성 검사
    if not validate_market_match(req.stock_code, req.market):
        raise StockAPIException(status_code=400, detail=f"종목 코드 '{req.stock_code}'와 시장 '{req.market}'이(가) 일치하지 않습니다.")

    return get_stock_chart(req.stock_code, req.period, req.market)

@router.get("/generate-audio")
def generate_audio_by_stock(
    code: str = Query(..., description="야후 파이낸스 형식의 종목 코드 (예: 005930.KS, TSLA)"),
    period: str = Query("1mo", description="차트 기간 (예: 1mo, 3mo 등)"),
    market: str = Query(None, description="시장 구분 (KR | US), 생략 시 자동 추론")
):
    # 시장 추론
    final_market = market or infer_market(code)

    # 유효성 검사
    if not validate_market_match(code, final_market):
        raise StockAPIException(status_code=400, detail="시장/코드 불일치")

    # 차트 데이터 가져오기
    chart_data = get_stock_chart(code, period, final_market)
    if not chart_data or len(chart_data) == 0:
        raise StockAPIException(status_code=404, detail="차트 데이터 없음")

    # 고유 파일 이름 생성
    uid = uuid.uuid4().hex
    json_file = f"stock_data_{uid}.json"
    wav_file = f"output_{uid}.wav"

    # JSON 파일로 저장
    with open(json_file, "w") as f:
        json.dump(chart_data, f)

    # C++ 실행
    result = subprocess.run(["wine", "./app/api/hrtf_converter.exe", json_file, wav_file])

    # 실패 시
    if result.returncode != 0 or not os.path.exists(wav_file):
        raise StockAPIException(status_code=500, detail="HRTF 변환 실패")

    # WAV 반환
    with open(wav_file, "rb") as f:
        audio_bytes = f.read()

    # 임시 파일 삭제
    os.remove(json_file)
    os.remove(wav_file)

    return Response(content=audio_bytes, media_type="audio/wav")
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

    
@router.websocket("/ws/trade-price")
async def websocket_trade_price(websocket: WebSocket):
    await websocket.accept()
    manager = connection_manager()

    try:
        while True:
            # 클라이언트로부터 메시지(예: 구독/구독 취소)를 기다립니다.
            message_text = await websocket.receive_text()
            data = json.loads(message_text)
            action = data.get('action')
            stock_code = data.get('code')

            if action == 'subscribe' and stock_code:
                await manager.subscribe(websocket, stock_code)
            elif action == 'unsubscribe' and stock_code:
                await manager.unsubscribe(websocket, stock_code)
            else:
                # 선택 사항: 알 수 없는 작업에 대한 오류를 다시 보냅니다.
                await websocket.send_json({
                    "status": "error",
                    "detail": f"Unknown action '{action}' or missing code."
                })

    except WebSocketDisconnect:
        print(f"Client {websocket} disconnected.")
    except Exception as e:
        print(f"An error occurred with client {websocket}: {e}")
    finally:
        # 클라이언트 연결이 끊어지면 구독을 정리합니다.
        await manager.handle_disconnect(websocket)
        print(f"Cleaned up subscriptions for client {websocket}.")

