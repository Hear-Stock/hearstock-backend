import os
import requests
import json
import time
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv


load_dotenv()
API_KEY = os.getenv("KIWOOM_REST_KEY")
SECRET_KEY = os.getenv("KIWOOM_REST_SECRET")
MY_ACCESS_TOKEN = os.getenv("KIWOOM_REST_TOKEN")

# 접근토큰 발급
def get_kiwoom_token():
	# 1. 요청할 API URL
	host = 'https://mockapi.kiwoom.com' # 모의투자
	# host = 'https://api.kiwoom.com' # 실전투자
	endpoint = '/oauth2/token'
	url =  host + endpoint

	# 2. header 데이터
	headers = {
		'Content-Type': 'application/json;charset=UTF-8', # 컨텐츠타입
	}

	# 요청 데이터
	params = {
		'grant_type': 'client_credentials',  # grant_type
		'appkey': API_KEY,  # 앱키
		'secretkey': SECRET_KEY,  # 시크릿키
	}

	# 3. http POST 요청
	response = requests.post(url, headers=headers, json=params)

	# 4. 응답 상태 코드와 데이터 출력
	print('Code:', response.status_code)
	print('Header:', json.dumps({key: response.headers.get(key) for key in ['next-key', 'cont-yn', 'api-id']}, indent=4, ensure_ascii=False))
	print('Body:', json.dumps(response.json(), indent=4, ensure_ascii=False))  # JSON 응답을 파싱하여 출력
	
	response = response.json()
	return response['token']

# 주식기본정보요청
def get_kiwoom_stkinfo(token, cont_yn='N', next_key='', code=""):
	# 1. 요청할 API URL
	host = 'https://mockapi.kiwoom.com' # 모의투자
	# host = 'https://api.kiwoom.com' # 실전투자
	endpoint = '/api/dostk/stkinfo'
	url =  host + endpoint

	# 2. header 데이터
	headers = {
		'Content-Type': 'application/json;charset=UTF-8', # 컨텐츠타입
		'authorization': f'Bearer {token}', # 접근토큰
		'cont-yn': cont_yn, # 연속조회여부
		'next-key': next_key, # 연속조회키
		'api-id': 'ka10001', # TR명
	}

	# 요청 데이터
	params = {
		'stk_cd': code, # 종목코드 거래소별 종목코드 (KRX:039490,NXT:039490_NX,SOR:039490_AL)
	}

	# 3. http POST 요청
	response = requests.post(url, headers=headers, json=params)

	# 4. 응답 상태 코드와 데이터 출력
	# print('Code:', response.status_code)
	# print('Header:', json.dumps({key: response.headers.get(key) for key in ['next-key', 'cont-yn', 'api-id']}, indent=4, ensure_ascii=False))
	# print('Body:', json.dumps(response.json(), indent=4, ensure_ascii=False))  # JSON 응답을 파싱하여 출력

	return response.json()


# 주식일주월시분요청
def fn_ka10005(token, cont_yn='N', next_key='', code=""):
	# 1. 요청할 API URL
	host = 'https://mockapi.kiwoom.com' # 모의투자
	# host = 'https://api.kiwoom.com' # 실전투자
	endpoint = '/api/dostk/mrkcond'
	url =  host + endpoint

	# 2. header 데이터
	headers = {
		'Content-Type': 'application/json;charset=UTF-8', # 컨텐츠타입
		'authorization': f'Bearer {token}', # 접근토큰
		'cont-yn': cont_yn, # 연속조회여부
		'next-key': next_key, # 연속조회키
		'api-id': 'ka10005', # TR명
	}

	# 2. 요청 데이터
	params = {
		'stk_cd': code, # 종목코드 거래소별 종목코드 (KRX:039490,NXT:039490_NX,SOR:039490_AL)
	}

	# 3. http POST 요청
	response = requests.post(url, headers=headers, json=params)

	# 4. 응답 상태 코드와 데이터 출력
	print('Code:', response.status_code)
	print('Header:', json.dumps({key: response.headers.get(key) for key in ['next-key', 'cont-yn', 'api-id']}, indent=4, ensure_ascii=False))
	print('Body:', json.dumps(response.json(), indent=4, ensure_ascii=False))  # JSON 응답을 파싱하여 출력


# 주식일봉차트조회요청
def fn_ka10081(token, cont_yn='N', next_key='', code="", date="20250501"):
	# 1. 요청할 API URL
	host = 'https://mockapi.kiwoom.com' # 모의투자
	# host = 'https://api.kiwoom.com' # 실전투자
	endpoint = '/api/dostk/chart'
	url =  host + endpoint

	# 2. header 데이터
	headers = {
		'Content-Type': 'application/json;charset=UTF-8', # 컨텐츠타입
		'authorization': f'Bearer {token}', # 접근토큰
		'cont-yn': cont_yn, # 연속조회여부
		'next-key': next_key, # 연속조회키
		'api-id': 'ka10081', # TR명
	}

	# 2. 요청 데이터
	params = {
		'stk_cd': code, # 종목코드 거래소별 종목코드 (KRX:039490,NXT:039490_NX,SOR:039490_AL)
		'base_dt': date, # 기준일자 YYYYMMDD
		'upd_stkpc_tp': '1', # 수정주가구분 0 or 1
	}

	# 3. http POST 요청
	response = requests.post(url, headers=headers, json=params)
	next_key_val = response.headers.get('next-key')
	# print(next_key_val)
	# 4. 응답 상태 코드와 데이터 출력
	# print('Code:', response.status_code)
	# print('Header:', json.dumps({key: response.headers.get(key) for key in ['next-key', 'cont-yn', 'api-id']}, indent=4, ensure_ascii=False))
	# print('Body:', json.dumps(response.json(), indent=4, ensure_ascii=False))  # JSON 응답을 파싱하여 출력

	data = response.json()  # 전체 응답을 딕셔너리로 파싱
	# print(data)
	# 필요한 부분만 반환
	return pd.DataFrame(data.get('stk_dt_pole_chart_qry', [])), next_key_val 

	# if next_key_val:
	# 	fn_ka10081(token=token, code=code, cont_yn='Y', next_key=next_key_val)

	

def get_kiwoom_chart(token, code, date=datetime.now().strftime("%Y%m%d")):
	all_data = []
	next_key_val = ""
	while True:
		time.sleep(0.5)
		data, next_key_val = fn_ka10081(token=token,
									   code=code,
									   date=date,
									   cont_yn='Y',
									   next_key=next_key_val)

		if data.empty:
			break
		all_data.append(data)  # extend가 아니라 append로 DataFrame 단위로 추가
		if not next_key_val:
			break

	if not all_data:
		return pd.DataFrame()
	
	all_data = pd.concat(all_data, ignore_index=True)  # DataFrame 리스트를 concat으로 합침
	
	all_data['cur_prc'] = all_data['cur_prc'].astype(float)
	all_data['prev_close'] = all_data['cur_prc'].shift(1)  # 바로 전 거래일 종가
	all_data['chg_rate'] = round(((all_data['cur_prc'] - all_data['prev_close']) / all_data['prev_close']) * 100, 2)

	df_filtered = all_data[['cur_prc', 'trde_qty', 'dt', 'open_pric', 'high_pric', 'low_pric', 'chg_rate']].copy()
	# 컬럼명 변경
	df_filtered.rename(columns={
		'open_pric': 'open',
		'cur_prc': 'close',
		'high_pric': 'high',
		'low_pric': 'low',
		'trde_qty': 'volume',
		'dt': 'timestamp'
	}, inplace=True)

	# 날짜 포맷으로 변환
	df_filtered['timestamp'] = pd.to_datetime(df_filtered['timestamp'], format='%Y%m%d')

	# 'open', 'close', 'high', 'low', 'volume' 컬럼을 숫자로 변환
	numeric_columns = ['open', 'close', 'high', 'low', 'volume']
	df_filtered[numeric_columns] = df_filtered[numeric_columns].apply(pd.to_numeric, errors='coerce')

	return df_filtered  # DataFrame 리스트를 concat으로 합침

# 주식년봉차트조회요청
def fn_ka10094(token, cont_yn='N', next_key='', code="", date=datetime.today().strftime('%Y%m%d')):
	# 1. 요청할 API URL
	host = 'https://mockapi.kiwoom.com' # 모의투자
	# host = 'https://api.kiwoom.com' # 실전투자
	endpoint = '/api/dostk/chart'
	url =  host + endpoint

	# 2. header 데이터
	headers = {
		'Content-Type': 'application/json;charset=UTF-8', # 컨텐츠타입
		'authorization': f'Bearer {token}', # 접근토큰
		'cont-yn': cont_yn, # 연속조회여부
		'next-key': next_key, # 연속조회키
		'api-id': 'ka10094', # TR명
	}

		# 2. 요청 데이터
	params = {
		'stk_cd': code, # 종목코드 거래소별 종목코드 (KRX:039490,NXT:039490_NX,SOR:039490_AL)
		'base_dt': date, # 기준일자 YYYYMMDD
		'upd_stkpc_tp': '1', # 수정주가구분 0 or 1
	}

	# 3. http POST 요청
	response = requests.post(url, headers=headers, json=params)

	# 4. 응답 상태 코드와 데이터 출력
	# print('Code:', response.status_code)
	# print('Header:', json.dumps({key: response.headers.get(key) for key in ['next-key', 'cont-yn', 'api-id']}, indent=4, ensure_ascii=False))
	# print('Body:', json.dumps(response.json(), indent=4, ensure_ascii=False))  # JSON 응답을 파싱하여 출력

	data = response.json()  # 전체 응답을 딕셔너리로 파싱

	df = pd.DataFrame(data)
	return df
	

# 실행 구간
if __name__ == '__main__':
	# 3. API 실행
	df = get_kiwoom_chart(token=get_kiwoom_token(), code="005930")
	print(type(df))

	stock_info = {
		"stk_cd": "종목코드",
		"stk_nm": "종목명",
		"setl_mm": "결산월",
		"fav": "액면가",
		"cap": "자본금",
		"flo_stk": "상장주식",
		"crd_rt": "신용비율",
		"oyr_hgst": "연중최고",
		"oyr_lwst": "연중최저",
		"mac": "시가총액",
		"mac_wght": "시가총액비중",
		"for_exh_rt": "외인소진률",
		"repl_pric": "대용가",
		"per": "PER",
		"eps": "EPS",
		"roe": "ROE",
		"pbr": "PBR",
		"ev": "EV",
		"bps": "BPS",
		"sale_amt": "매출액",
		"bus_pro": "영업이익",
		"cup_nga": "당기순이익",
		"250hgst": "250최고",
		"250lwst": "250최저",
		"high_pric": "고가",
		"open_pric": "시가",
		"low_pric": "저가",
		"upl_pric": "상한가",
		"lst_pric": "하한가",
		"base_pric": "기준가",
		"exp_cntr_pric": "예상체결가",
		"exp_cntr_qty": "예상체결수량",
		"250hgst_pric_dt": "250최고가일",
		"250hgst_pric_pre_rt": "250최고가대비율",
		"250lwst_pric_dt": "250최저가일",
		"250lwst_pric_pre_rt": "250최저가대비율",
		"cur_prc": "현재가",
		"pre_sig": "대비기호",
		"pred_pre": "전일대비",
		"flu_rt": "등락율",
		"trde_qty": "거래량",
		"trde_pre": "거래대비",
		"fav_unit": "액면가단위",
		"dstr_stk": "유통주식",
		"dstr_rt": "유통비율"
	}

	

