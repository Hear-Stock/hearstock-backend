import asyncio
import json
import websockets
from websockets.exceptions import ConnectionClosed
from collections import defaultdict
from fastapi import WebSocket
from websockets.protocol import State
import logging

logging.basicConfig(level=logging.INFO)


from app.api.kiwoomREST import get_kiwoom_token


# socket 정보
SOCKET_URL = 'wss://mockapi.kiwoom.com:10000/api/dostk/websocket'  # 모의투자 접속 URL

class KiwoomConnectionManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.kiwoom_ws = None
            cls._instance.access_token = None
            cls._instance.subscriptions = defaultdict(set)
            cls._instance.stock_to_grp = {}
            cls._instance.grp_to_stock = {}
            cls._instance.next_grp_no = 0
            cls._instance.is_running = False
            cls._instance.lock = asyncio.Lock()
            cls._instance.reader_task = None
        return cls._instance

    def _generate_grp_no(self) -> str:
        """4자리 문자열 형식에 맞게 그룹 번호를 생성합니다."""
        grp_no = str(self.next_grp_no).zfill(4)
        self.next_grp_no = (self.next_grp_no + 1) % 10000  # 그룹 번호 재사용
        return grp_no

    async def _login_to_kiwoom(self):
        """Kiwoom WebSocket 서버에 로그인합니다."""
        self.access_token = get_kiwoom_token()
        login_param = {
            'trnm': 'LOGIN',
            'token': self.access_token
        }
        await self.kiwoom_ws.send(json.dumps(login_param))
        login_response_str = await self.kiwoom_ws.recv()
        login_response = json.loads(login_response_str)
        
        if login_response.get('trnm') == 'LOGIN' and login_response.get('return_code') == 0:
            print('Kiwoom 로그인 성공하였습니다.')
            return True
        else:
            msg = login_response.get("return_msg", "알 수 없는 로그인 오류")
            print(f'Kiwoom 로그인 실패하였습니다: {msg}')
            return False

    async def connect(self):
        """Kiwoom에 연결하고, 로그인한 후, 백그라운드 리더 작업을 시작합니다."""
        if self.is_running:
            return True
        try:
            print("첫 구독자 발생. Kiwoom 서버에 연결을 시도합니다...")
            self.kiwoom_ws = await websockets.connect(SOCKET_URL)
            print("Kiwoom WebSocket 서버에 연결되었습니다.")

            if await self._login_to_kiwoom():
                self.is_running = True
                self.reader_task = asyncio.create_task(self._kiwoom_reader_task())
                print("Kiwoom 연결이 수립되었고, 데이터 리더 작업을 시작합니다.")
                # 재연결 시, 기존 구독 재등록
                await self._resubscribe_all()
                return True
            else:
                await self.kiwoom_ws.close()
                return False
        except Exception as e:
            print(f"Kiwoom 연결 관리 중 예기치 않은 오류 발생: {e}")
            self.is_running = False
            return False

    async def disconnect(self):
        """Kiwoom과의 연결을 종료합니다."""
        if not self.is_running:
            return
        
        print("마지막 구독자 이탈. Kiwoom 서버와의 연결을 종료합니다.")
        self.is_running = False
        
        if self.reader_task:
            self.reader_task.cancel()
            self.reader_task = None
        
        if self.kiwoom_ws and self.kiwoom_ws.protocol.state != State.CLOSED:
            try:
                await self.kiwoom_ws.close()
                print("Kiwoom WebSocket 연결이 성공적으로 종료되었습니다.")
            except Exception as e:
                print(f"Kiwoom WebSocket 연결 종료 중 오류 발생: {e}")
        
        # 모든 구독 정보 초기화 (연결이 끊겼으므로)
        self.stock_to_grp.clear()
        self.grp_to_stock.clear()
        self.next_grp_no = 0


    async def _resubscribe_all(self):
        """서버 재연결 시, 기존에 클라이언트들이 구독하고 있던 모든 종목을 재등록합니다."""
        # stock_to_grp에 있는 모든 종목에 대해 다시 REG 요청
        for stock_code, grp_no in self.stock_to_grp.items():
            print(f"재구독: {stock_code} (grp_no: {grp_no})")
            reg_msg = {
                'trnm': 'REG',
                'grp_no': grp_no,
                'refresh': '1',
                'data': [{'item': [stock_code.split('.')[0]], 'type': ['0B']}]
            }
            try:
                await self.kiwoom_ws.send(json.dumps(reg_msg))
            except Exception as e:
                print(f"{stock_code} 재구독 실패: {e}")


    async def _kiwoom_reader_task(self):
        """Kiwoom API로부터 오는 메시지를 계속 읽고 클라이언트에게 배포합니다."""
        print("Kiwoom 데이터 리더 작업을 시작합니다.")
        try:
            while self.is_running:
                message = await self.kiwoom_ws.recv()
                data = json.loads(message)
                print(self.subscriptions)
                if data.get('trnm') == 'PING':
                    await self.kiwoom_ws.send(message)
                    continue

                if data.get('trnm') == 'REAL':
                    for info_map in data.get('data', []):
                        current_stock_code = info_map.get('item')

                        if info_map.get('name') == "주식체결":
                            tick_info_map = info_map.get('values', {})
                            체결시간 = tick_info_map.get('20', '')
                            현재가 = abs(float(tick_info_map.get('10', 0)))
                            전일대비 = float(tick_info_map.get('11', 0))
                            등락률 = float(tick_info_map.get('12', 0))
                            체결량 = int(tick_info_map.get('15', 0))
                            logging.info(f"--- 실시간 체결 정보 ---\n체결시간: {체결시간}\n현재가: {현재가}\n전일대비: {전일대비}\n등락률: {등락률}\n체결량: {체결량}\n--------------------")
                            
                            trade_info = {
                                "stock_code": current_stock_code,
                                "execution_time": tick_info_map.get('20', ''),
                                "current_price": abs(float(tick_info_map.get('10', 0))),
                                "change": float(tick_info_map.get('11', 0)),
                                "fluctuation_rate": float(tick_info_map.get('12', 0)),
                                "volume": int(tick_info_map.get('15', 0))
                            }
                            
                            
                            new_message = json.dumps(trade_info)
                            print(new_message)
                            print(self.subscriptions[current_stock_code+".KS"])
                            await asyncio.gather(*[
                                client.send_text(new_message)
                                for client in self.subscriptions[current_stock_code+".KS"] # 임시로 .KS 추가
                            ])
        except ConnectionClosed:
            print("리더 작업 중 Kiwoom 연결이 끊겼습니다.")
        except asyncio.CancelledError:
            print("리더 작업이 정상적으로 취소되었습니다.")
        except Exception as e:
            print(f"리더 작업 중 오류 발생: {e}")
        finally:
            self.is_running = False
            print("Kiwoom 데이터 리더 작업을 종료합니다.")


    async def subscribe(self, client_ws: WebSocket, stock_code: str):
        """클라이언트의 종목 구독 요청을 처리합니다."""
        async with self.lock:
            # 첫 구독자라면 Kiwoom에 연결
            if not self.is_running:
                if not await self.connect():
                    await client_ws.send_json({"status": "error", "detail": "Kiwoom 서버 연결에 실패했습니다."})
                    return

            is_first_subscription_for_stock = not self.subscriptions[stock_code]
            self.subscriptions[stock_code].add(client_ws)
            print(f"Client {client_ws} subscribed to {stock_code}. Total subscribers: {len(self.subscriptions[stock_code])}")

            if is_first_subscription_for_stock:
                grp_no = self._generate_grp_no()
                self.stock_to_grp[stock_code] = grp_no
                self.grp_to_stock[grp_no] = stock_code
                
                print(f"First subscription for {stock_code}. Assigning grp_no: {grp_no}")

                reg_msg = {
                    'trnm': 'REG',
                    'grp_no': grp_no,
                    'refresh': '1',
                    'data': [{'item': [stock_code.split('.')[0]], 'type': ['0B']}]
                }
                if self.is_running and self.kiwoom_ws.protocol.state != State.CLOSED:
                    await self.kiwoom_ws.send(json.dumps(reg_msg))
                else:
                    print("Kiwoom이 연결되지 않아 구독 요청을 보낼 수 없습니다.")

    async def unsubscribe(self, client_ws: WebSocket, stock_code: str):
        """클라이언트의 종목 구독 해지 요청을 처리합니다."""
        async with self.lock:
            if client_ws not in self.subscriptions.get(stock_code, set()):
                return

            self.subscriptions[stock_code].remove(client_ws)
            print(f"Client {client_ws} unsubscribed from {stock_code}.")

            if not self.subscriptions[stock_code]:
                del self.subscriptions[stock_code]
                grp_no = self.stock_to_grp.pop(stock_code, None)
                if grp_no:
                    self.grp_to_stock.pop(grp_no, None)
                    print(f"All clients for {stock_code} unsubscribed. Removing grp_no: {grp_no}")

                    remove_msg = {'trnm': 'REMOVE', 'grp_no': grp_no}
                    if self.is_running and self.kiwoom_ws.protocol.state != State.CLOSED:
                        await self.kiwoom_ws.send(json.dumps(remove_msg))
                    else:
                        print("Kiwoom이 연결되지 않아 구독 해지 요청을 보낼 수 없습니다.")
            
            # 마지막 구독자였는지 확인
            if not any(self.subscriptions.values()):
                await self.disconnect()


    async def handle_disconnect(self, client_ws: WebSocket):
        """클라이언트의 연결 종료를 처리합니다."""
        disconnected_subscriptions = []
        async with self.lock:
            for stock_code, clients in self.subscriptions.items():
                if client_ws in clients:
                    disconnected_subscriptions.append(stock_code)
        
        for stock_code in disconnected_subscriptions:
            await self.unsubscribe(client_ws, stock_code)