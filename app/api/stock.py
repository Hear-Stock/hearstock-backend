from fastapi import APIRouter, Query, Response, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
import os
import subprocess
import uuid
import json
import asyncio
import websockets
from websockets.protocol import State 

from app.services.stock_service import get_stock_chart, get_price, get_overseas_price
from app.api.kiwoomREST import get_kiwoom_token,get_stock_code, get_stocks_by_keyword


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
        return Response(content="시장/코드 불일치", status_code=400)

    # 차트 데이터 가져오기
    chart_data = get_stock_chart(code, period, final_market)
    if not chart_data or len(chart_data) == 0:
        return Response(content="차트 데이터 없음", status_code=404)

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
        return Response(content="HRTF 변환 실패", status_code=500)

    # WAV 반환
    with open(wav_file, "rb") as f:
        audio_bytes = f.read()

    # 임시 파일 삭제
    os.remove(json_file)
    os.remove(wav_file)

    return Response(content=audio_bytes, media_type="audio/wav")

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


# socket 정보
SOCKET_URL = 'wss://mockapi.kiwoom.com:10000/api/dostk/websocket'  # 모의투자 접속 URL
# SOCKET_URL = 'wss://api.kiwoom.com:10000/api/dostk/websocket'  # 접속 URL

class KiwoomWebSocketProxy:
    def __init__(self, client_ws: WebSocket):
        self.client_ws = client_ws
        self.kiwoom_ws = None
        self.is_running = False
        self.registered_groups = set()

    async def connect_to_kiwoom(self):
        try:
            print("Kiwoom WebSocket 서버에 연결을 시도합니다...")
            self.kiwoom_ws = await websockets.connect(SOCKET_URL)
            print("Kiwoom WebSocket 서버에 연결되었습니다.")
            return True
        except Exception as e:
            print(f"Kiwoom WebSocket 서버 연결 실패: {e}")
            await self.client_ws.send_json({"status": "error", "detail": f"Kiwoom 연결 실패: {e}"})
            return False

    async def login_to_kiwoom(self):
        login_param = {
            'trnm': 'LOGIN',
            'token': ACCESS_TOKEN
        }
        print(ACCESS_TOKEN)
        await self.kiwoom_ws.send(json.dumps(login_param))
        login_response = json.loads(await self.kiwoom_ws.recv())
        
        if login_response.get('trnm') == 'LOGIN' and login_response.get('return_code') == 0:
            print('Kiwoom 로그인 성공하였습니다.')
            await self.client_ws.send_json({"status": "Kiwoom 로그인 성공"})
            return True
        else:
            msg = login_response.get("return_msg", "알 수 없는 로그인 오류")
            print(f'Kiwoom 로그인 실패하였습니다: {msg}')
            await self.client_ws.send_json({"status": "Kiwoom 로그인 실패", "detail": msg})
            return False

    async def _kiwoom_to_client_task(self):
        while self.is_running:
            try:
                message = await self.kiwoom_ws.recv()

                try:
                    data = json.loads(message)
                    if data.get('trnm') == 'REAL':
                        for info_map in data.get('data', []):
                            if info_map.get('name') == "주식체결":
                                tick_info_map = info_map['values']
                                체결시간 = tick_info_map.get('20', '')
                                현재가 = abs(float(tick_info_map.get('10', 0)))
                                전일대비 = float(tick_info_map.get('11', 0))
                                등락률 = float(tick_info_map.get('12', 0))
                                체결량 = int(tick_info_map.get('15', 0))
                                print(f"--- 실시간 체결 정보 ---\n체결시간: {체결시간}\n현재가: {현재가}\n전일대비: {전일대비}\n등락률: {등락률}\n체결량: {체결량}\n--------------------")
                                
                except (json.JSONDecodeError, KeyError, ValueError) as e:
                    print(f"실시간 체결 정보 파싱 오류: {e}")

                await self.client_ws.send_text(message)
            except websockets.ConnectionClosed:
                print("Kiwoom WebSocket 연결이 닫혔습니다.")
                break
            except Exception as e:
                if self.is_running:
                    print(f"Kiwoom에서 클라이언트로 전달 중 오류 발생: {e}")
                break
        self.is_running = False

    async def _client_to_kiwoom_task(self):
        while self.is_running:
            try:
                message_text = await self.client_ws.receive_text()
                print(f"클라이언트로부터 메시지 수신: {message_text}")
                
                try:
                    message_data = json.loads(message_text)
                    trnm = message_data.get('trnm')
                    grp_no = message_data.get('grp_no')
                    if trnm == 'REG' and grp_no:
                        self.registered_groups.add(grp_no)
                        print(f"구독 그룹 추가: {grp_no}, 현재 그룹: {self.registered_groups}")
                    elif trnm == 'REMOVE' and grp_no:
                        self.registered_groups.discard(grp_no)
                        print(f"구독 그룹 제거: {grp_no}, 현재 그룹: {self.registered_groups}")
                except json.JSONDecodeError:
                    pass # JSON 형식이 아니면 그냥 전달

                await self.kiwoom_ws.send(message_text)
            except WebSocketDisconnect:
                print("클라이언트가 FastAPI WebSocket에서 연결을 끊었습니다.")
                break
            except Exception as e:
                if self.is_running:
                    print(f"클라이언트에서 Kiwoom으로 전달 중 오류 발생: {e}")
                break
        self.is_running = False

    async def run(self):
        if not await self.connect_to_kiwoom():
            return

        if not await self.login_to_kiwoom():
            await self.disconnect()
            return
            
        self.is_running = True
        
        kiwoom_reader = asyncio.create_task(self._kiwoom_to_client_task())
        client_reader = asyncio.create_task(self._client_to_kiwoom_task())
        
        # 두 작업 중 하나가 완료될 때까지 대기
        _, pending = await asyncio.wait(
            [kiwoom_reader, client_reader],
            return_when=asyncio.FIRST_COMPLETED,
        )

        # 깔끔한 종료를 위해 대기 중인 작업 취소
        for task in pending:
            task.cancel()
        
        await self.disconnect()

    async def disconnect(self):
        self.is_running = False
        
        if self.kiwoom_ws and self.kiwoom_ws.state != State.CLOSED:
            if self.registered_groups:
                print(f"저장된 모든 그룹({self.registered_groups})에 대해 구독 해지를 시도합니다.")
                for grp_no in list(self.registered_groups):
                    unsub_msg = json.dumps({
                        'trnm': 'REMOVE',
                        'grp_no': grp_no,
                    })
                    try:
                        await self.kiwoom_ws.send(unsub_msg)
                        print(f"그룹 {grp_no} 구독 해지 메시지 전송 완료.")
                    except Exception as e:
                        print(f"그룹 {grp_no} 구독 해지 메시지 전송 중 오류 발생: {e}")
            
            await self.kiwoom_ws.close()
            print("Kiwoom WebSocket 서버와 연결이 끊어졌습니다.")
        print("프록시 작업이 종료되었습니다.")


@router.websocket("/ws/trade-price")
async def websocket_trade_price(websocket: WebSocket):
    await websocket.accept()
    proxy = KiwoomWebSocketProxy(websocket)
    try:
        await proxy.run()
    except Exception as e:
        # 프록시 실행 중 예기치 않은 오류 기록
        print(f"WebSocket 프록시에서 예기치 않은 오류 발생: {e}")
    finally:
        # 클라이언트 연결을 정상적으로 닫도록 보장
        print("클라이언트와의 FastAPI WebSocket 연결이 닫혔습니다.")

