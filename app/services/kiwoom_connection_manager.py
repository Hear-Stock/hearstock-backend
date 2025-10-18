import asyncio
import json
import websockets
from websockets.exceptions import ConnectionClosed
from collections import defaultdict
from fastapi import WebSocket


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
        return cls._instance

    def _generate_grp_no(self) -> str:
        """4자리 문자열 형식에 맞게 그룹 번호를 생성합니다."""
        grp_no = str(self.next_grp_no).zfill(4)
        self.next_grp_no += 1
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

    async def connect_and_manage(self):
        """
        Kiwoom API에 연결하고, 재연결을 관리하며,
        백그라운드에서 실시간 데이터를 읽는 작업을 시작합니다.
        """
        while True:
            try:
                print("Kiwoom WebSocket 서버에 연결을 시도합니다...")
                self.kiwoom_ws = await websockets.connect(SOCKET_URL)
                print("Kiwoom WebSocket 서버에 연결되었습니다.")

                if await self._login_to_kiwoom():
                    self.is_running = True
                    # 연결 성공 시, 기존 구독 모두 재등록
                    await self._resubscribe_all()
                    # 백그라운드 리더 작업 시작
                    await self._kiwoom_reader_task()
                else:
                    await self.kiwoom_ws.close()

            except (ConnectionClosed, ConnectionRefusedError) as e:
                print(f"Kiwoom WebSocket 연결이 끊어졌습니다: {e}. 5초 후 재연결합니다.")
                self.is_running = False
            except Exception as e:
                print(f"Kiwoom 연결 관리 중 예기치 않은 오류 발생: {e}")
                self.is_running = False
            
            await asyncio.sleep(5)

    async def _resubscribe_all(self):
        """서버 재연결 시, 기존에 클라이언트들이 구독하고 있던 모든 종목을 재등록합니다."""
        async with self.lock:
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
        while self.is_running:
            try:
                message = await self.kiwoom_ws.recv()
                data = json.loads(message)
                
                if data.get('trnm') == 'REAL':
                    grp_no = data.get('grp_no')
                    stock_code = self.grp_to_stock.get(grp_no)
                    
                    if stock_code and stock_code in self.subscriptions:
                        # 클라이언트에게 보낼 메시지에 stock_code 정보를 추가하면 더 유용함
                        data['stock_code'] = stock_code
                        enriched_message = json.dumps(data)
                        
                        # asyncio.gather를 사용하여 동시 전송
                        await asyncio.gather(*[
                            client.send_text(enriched_message)
                            for client in self.subscriptions[stock_code]
                        ])
            except ConnectionClosed:
                print("리더 작업 중 Kiwoom 연결이 끊겼습니다.")
                self.is_running = False
                break
            except Exception as e:
                print(f"리더 작업 중 오류 발생: {e}")
                if not self.kiwoom_ws.open:
                    self.is_running = False
                    break

    async def subscribe(self, client_ws: WebSocket, stock_code: str):
        """클라이언트의 종목 구독 요청을 처리합니다."""
        async with self.lock:
            is_first_subscription = not self.subscriptions[stock_code]
            
            self.subscriptions[stock_code].add(client_ws)
            print(f"Client {client_ws} subscribed to {stock_code}. Total subscribers: {len(self.subscriptions[stock_code])}")

            if is_first_subscription:
                grp_no = self._generate_grp_no()
                self.stock_to_grp[stock_code] = grp_no
                self.grp_to_stock[grp_no] = grp_no
                
                print(f"First subscription for {stock_code}. Assigning grp_no: {grp_no}")

                reg_msg = {
                    'trnm': 'REG',
                    'grp_no': grp_no,
                    'refresh': '1',
                    'data': [{'item': [stock_code.split('.')[0]], 'type': ['0B']}]
                }
                if self.is_running and self.kiwoom_ws.open:
                    await self.kiwoom_ws.send(json.dumps(reg_msg))
                else:
                    print("Kiwoom이 연결되지 않아 구독 요청을 보낼 수 없습니다.")

    async def unsubscribe(self, client_ws: WebSocket, stock_code: str):
        """클라이언트의 종목 구독 해지 요청을 처리합니다."""
        async with self.lock:
            if client_ws in self.subscriptions.get(stock_code, set()):
                self.subscriptions[stock_code].remove(client_ws)
                print(f"Client {client_ws} unsubscribed from {stock_code}.")

                if not self.subscriptions[stock_code]:
                    del self.subscriptions[stock_code]
                    grp_no = self.stock_to_grp.pop(stock_code, None)
                    if grp_no:
                        del self.grp_to_stock[grp_no]
                        print(f"All clients for {stock_code} unsubscribed. Removing grp_no: {grp_no}")

                        remove_msg = {'trnm': 'REMOVE', 'grp_no': grp_no}
                        if self.is_running and self.kiwoom_ws.open:
                            await self.kiwoom_ws.send(json.dumps(remove_msg))
                        else:
                            print("Kiwoom이 연결되지 않아 구독 해지 요청을 보낼 수 없습니다.")

    async def handle_disconnect(self, client_ws: WebSocket):
        """클라이언트의 연결 종료를 처리합니다."""
        async with self.lock:
            disconnected_subscriptions = []
            for stock_code, clients in self.subscriptions.items():
                if client_ws in clients:
                    disconnected_subscriptions.append(stock_code)
            
            # Use a copy of the list to iterate over, as unsubscribe will modify the dictionary
            for stock_code in disconnected_subscriptions:
                await self.unsubscribe(client_ws, stock_code)
