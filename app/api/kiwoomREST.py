import os
import requests
import json
import time
import redis
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv
from app.db.redis_service import get_redis, get_cache, set_cache


load_dotenv()
API_KEY = os.getenv("KIWOOM_REST_KEY")
SECRET_KEY = os.getenv("KIWOOM_REST_SECRET")

REDIS_HOST = os.getenv("REDIS_HOST")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))


# 공통 post 함수 
def try_post(url, headers, params, timeout=5):
	try:
		response = requests.post(url, headers=headers, json=params, timeout=timeout)
		response.raise_for_status()
		return response.json()
	except requests.exceptions.RequestException as e:
		return {"error": f"요청 실패: {str(e)}"}


# 접근토큰 발급
def get_kiwoom_token():
	cache_key = f"KIWOOM_TOKEN"
	r = get_redis(9)
	# Redis에서 토큰 조회
	token = get_cache(r, cache_key)

	if token:
		return token
	
	# 1. 요청할 API URL
	host = 'https://mockapi.kiwoom.com'  # 모의투자
	# host = 'https://api.kiwoom.com' # 실전투자
	endpoint = '/oauth2/token'
	url = host + endpoint

	# 2. header 데이터
	headers = {
		'Content-Type': 'application/json;charset=UTF-8',  # 컨텐츠타입
	}

	# 요청 데이터
	params = {
		'grant_type': 'client_credentials',  # grant_type
		'appkey': API_KEY,  # 앱키
		'secretkey': SECRET_KEY,  # 시크릿키
	}

	response = try_post(url, headers, params)

	if "error" in response:
		return {"error": f"토큰 요청 실패: {response['error']}"}

	try:
		token = response["token"]
		set_cache(r, cache_key, token, 3600)
		return token
	except (KeyError, redis.RedisError) as e:
		return {"error": f"토큰 저장 또는 응답 파싱 실패: {str(e)}"}


# 주식기본정보요청
def get_kiwoom_stkinfo(token, cont_yn='N', next_key='', code=""):
	# 1. 요청할 API URL
	host = 'https://mockapi.kiwoom.com'  # 모의투자
	# host = 'https://api.kiwoom.com' # 실전투자
	endpoint = '/api/dostk/stkinfo'
	url = host + endpoint

	# 2. header 데이터
	headers = {
		'Content-Type': 'application/json;charset=UTF-8',  # 컨텐츠타입
		'authorization': f'Bearer {token}',  # 접근토큰
		'cont-yn': cont_yn,  # 연속조회여부
		'next-key': next_key,  # 연속조회키
		'api-id': 'ka10001',  # TR명
	}

	# 요청 데이터
	params = {
		'stk_cd': code,  # 종목코드 거래소별 종목코드 (KRX:039490,NXT:039490_NX,SOR:039490_AL)
	}

	# 3. http POST 요청
	response = try_post(url, headers, params)

	if "error" in response:
		return {"error": f"기본 정보 조회 실패: {response['error']}"}
	return response


# 일봉차트 전체 조회
def get_kiwoom_stock_chart(token, code, date=datetime.now().strftime("%Y%m%d")):
	r = get_redis(0)
	cached = get_cache(r, code)
	if cached:
		return pd.read_json(cached)

	host = 'https://mockapi.kiwoom.com'
	endpoint = '/api/dostk/chart'
	url = host + endpoint
	all_data = []
	next_key_val = ""

	while True:
		headers = {
			'Content-Type': 'application/json;charset=UTF-8',
			'authorization': f'Bearer {token}',
			'cont-yn': 'Y',
			'next-key': next_key_val,
			'api-id': 'ka10081',
		}

		params = {
			'stk_cd': code,
			'base_dt': date,
			'upd_stkpc_tp': '1',
		}

		try:
			response = requests.post(url, headers=headers, json=params, timeout=5)
			response.raise_for_status()
			data_json = response.json()
		except requests.exceptions.RequestException as e:
			print(f"[ERROR] 요청 실패: {e}")
			response.failure(f"error: {e}")
			return None

		next_key_val = response.headers.get("next-key")
		data = data_json.get("stk_dt_pole_chart_qry", [])

		if not data:
			break

		df = pd.DataFrame(data)
		if df.empty:
			break
		all_data.append(df)

		if not next_key_val:
			break

		time.sleep(1)

	if not all_data:
		return pd.DataFrame()

	df = pd.concat(all_data, ignore_index=True)

	try:
		df['cur_prc'] = df['cur_prc'].astype(float)
		df['prev_close'] = df['cur_prc'].shift(1)
		df['chg_rate'] = round(((df['cur_prc'] - df['prev_close']) / df['prev_close']) * 100, 2)

		df_filtered = df[['cur_prc', 'trde_qty', 'dt', 'open_pric', 'high_pric', 'low_pric', 'chg_rate']].copy()
		df_filtered.rename(columns={
			'open_pric': 'open',
			'cur_prc': 'close',
			'high_pric': 'high',
			'low_pric': 'low',
			'trde_qty': 'volume',
			'dt': 'timestamp'
		}, inplace=True)

		df_filtered['timestamp'] = pd.to_datetime(df_filtered['timestamp'], format='%Y%m%d')
		df_filtered['timestamp'] = df_filtered['timestamp'].dt.strftime('%Y-%m-%dT%H:%M:%S')

		numeric_columns = ['open', 'close', 'high', 'low', 'volume', 'chg_rate']
		df_filtered = df_filtered.where(pd.notnull(df_filtered), "0")
		df_filtered[numeric_columns] = df_filtered[numeric_columns].apply(pd.to_numeric, errors='coerce')

		# 변환 후 캐싱
		set_cache(r, code, df_filtered.to_json())

		return df_filtered

	except Exception as e:
		print(f"[ERROR] 데이터 가공 실패: {e}")
	
	return pd.DataFrame()


# 주식년봉차트조회요청
def fn_ka10094(token, cont_yn='N', next_key='', code="", date=datetime.today().strftime('%Y%m%d')):
	# 1. 요청할 API URL
	host = 'https://mockapi.kiwoom.com'  # 모의투자
	# host = 'https://api.kiwoom.com' # 실전투자
	endpoint = '/api/dostk/chart'
	url = host + endpoint

	# 2. header 데이터
	headers = {
		'Content-Type': 'application/json;charset=UTF-8',  # 컨텐츠타입
		'authorization': f'Bearer {token}',  # 접근토큰
		'cont-yn': cont_yn,  # 연속조회여부
		'next-key': next_key,  # 연속조회키
		'api-id': 'ka10094',  # TR명
	}

	# 2. 요청 데이터
	params = {
		'stk_cd': code,  # 종목코드 거래소별 종목코드 (KRX:039490,NXT:039490_NX,SOR:039490_AL)
		'base_dt': date,  # 기준일자 YYYYMMDD
		'upd_stkpc_tp': '1',  # 수정주가구분 0 or 1
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


# 전업종지수요청
def get_industry_price(token, code, cont_yn='N', next_key=''):
	# 1. 요청할 API URL
	host = 'https://mockapi.kiwoom.com'  # 모의투자
	# host = 'https://api.kiwoom.com' # 실전투자
	endpoint = '/api/dostk/sect'
	url = host + endpoint

	# 2. header 데이터
	headers = {
		'Content-Type': 'application/json;charset=UTF-8',  # 컨텐츠타입
		'authorization': f'Bearer {token}',  # 접근토큰
		'cont-yn': cont_yn,  # 연속조회여부
		'next-key': next_key,  # 연속조회키
		'api-id': 'ka20003',  # TR명
	}

	# 2. 요청 데이터
	params = {
		'inds_cd': code,
		# 업종코드 001:종합(KOSPI), 002:대형주, 003:중형주, 004:소형주 101:종합(KOSDAQ), 201:KOSPI200, 302:KOSTAR, 701: KRX100 나머지 ※ 업종코드 참고
	}

	# 3. http POST 요청
	response = try_post(url, headers, params)

	if "error" in response:
		return {"error": f"기본 정보 조회 실패: {response['error']}"}
	return response


# 테마그룹별요청
def fn_ka90001(token, code='', cont_yn='N', next_key=''):
	# 1. 요청할 API URL
	host = 'https://mockapi.kiwoom.com'  # 모의투자
	# host = 'https://api.kiwoom.com' # 실전투자
	endpoint = '/api/dostk/thme'
	url = host + endpoint

	# 2. header 데이터
	headers = {
		'Content-Type': 'application/json;charset=UTF-8',  # 컨텐츠타입
		'authorization': f'Bearer {token}',  # 접근토큰
		'cont-yn': cont_yn,  # 연속조회여부
		'next-key': next_key,  # 연속조회키
		'api-id': 'ka90001',  # TR명
	}

	# 2. 요청 데이터
	params = {
		'qry_tp': '2',  # 검색구분 0:전체검색, 1:테마검색, 2:종목검색
		'stk_cd': code,  # 종목코드 검색하려는 종목코드
		'date_tp': '10',  # 날짜구분 n일전 (1일 ~ 99일 날짜입력)
		'thema_nm': '',  # 테마명 검색하려는 테마명
		'flu_pl_amt_tp': '1',  # 등락수익구분 1:상위기간수익률, 2:하위기간수익률, 3:상위등락률, 4:하위등락률
		'stex_tp': '1',  # 거래소구분 1:KRX, 2:NXT 3.통합
	}

	# 3. http POST 요청
	response = requests.post(url, headers=headers, json=params)
	next_key_val = response.headers.get('next-key')
	print(next_key_val)
	print(response.text)


	# 4. 응답 상태 코드와 데이터 출력
	# print('Code:', response.status_code)s
	# print('Header:', json.dumps({key: response.headers.get(key) for key in ['next-key', 'cont-yn', 'api-id']}, indent=4, ensure_ascii=False))
	# print('Body:', json.dumps(response.json(), indent=4, ensure_ascii=False))  # JSON 응답을 파싱하여 출력


# 테마구성종목요청
def fn_ka90002(token, code, cont_yn='N', next_key=''):
	# 1. 요청할 API URL
	host = 'https://mockapi.kiwoom.com'  # 모의투자
	# host = 'https://api.kiwoom.com' # 실전투자
	endpoint = '/api/dostk/thme'
	url = host + endpoint

	# 2. header 데이터
	headers = {
		'Content-Type': 'application/json;charset=UTF-8',  # 컨텐츠타입
		'authorization': f'Bearer {token}',  # 접근토큰
		'cont-yn': cont_yn,  # 연속조회여부
		'next-key': next_key,  # 연속조회키
		'api-id': 'ka90002',  # TR명
	}

	# 2. 요청 데이터
	params = {
		'date_tp': '99',  # 날짜구분 1일 ~ 99일 날짜입력
		'thema_grp_cd': code,  # 테마그룹코드 테마그룹코드 번호
		'stex_tp': '1',  # 거래소구분 1:KRX, 2:NXT 3.통합
	}

	# 3. http POST 요청
	response = requests.post(url, headers=headers, json=params)
	next_key_val = response.headers.get('next-key')
	print(next_key_val)

	# 4. 응답 상태 코드와 데이터 출력
	print('Code:', response.status_code)
	print('Header:', json.dumps({key: response.headers.get(key) for key in ['next-key', 'cont-yn', 'api-id']}, indent=4,
								ensure_ascii=False))
	print('Body:', json.dumps(response.json(), indent=4, ensure_ascii=False))  # JSON 응답을 파싱하여 출력


# 업종별주가요청
def fn_ka20002(token, cont_yn='N', next_key=''):
	# 1. 요청할 API URL
	host = 'https://mockapi.kiwoom.com'  # 모의투자
	# host = 'https://api.kiwoom.com' # 실전투자
	endpoint = '/api/dostk/sect'
	url = host + endpoint

	# 2. header 데이터
	headers = {
		'Content-Type': 'application/json;charset=UTF-8',  # 컨텐츠타입
		'authorization': f'Bearer {token}',  # 접근토큰
		'cont-yn': cont_yn,  # 연속조회여부
		'next-key': next_key,  # 연속조회키
		'api-id': 'ka20002',  # TR명
	}

	# 2. 요청 데이터
	params = {
		'mrkt_tp': '0',  # 시장구분 0:코스피, 1:코스닥, 2:코스피200
		'inds_cd': '018',
		# 업종코드 001:종합(KOSPI), 002:대형주, 003:중형주, 004:소형주 101:종합(KOSDAQ), 201:KOSPI200, 302:KOSTAR, 701: KRX100 나머지 ※ 업종코드 참고
		'stex_tp': '1',  # 거래소구분 1:KRX, 2:NXT, 3:통합
	}

	# 3. http POST 요청
	response = requests.post(url, headers=headers, json=params)
	next_key_val = response.headers.get('next-key')
	print(next_key_val)
	print(response.text)


	# 4. 응답 상태 코드와 데이터 출력
	# print('Code:', response.status_code)
	# print('Header:', json.dumps({key: response.headers.get(key) for key in ['next-key', 'cont-yn', 'api-id']}, indent=4, ensure_ascii=False))
	# print('Body:', json.dumps(response.json(), indent=4, ensure_ascii=False))  # JSON 응답을 파싱하여 출력


# 종목코드 조회 함수
def get_stock_code(token, company_name, market='0'):
	# 1. 요청할 API URL
	host = 'https://mockapi.kiwoom.com'  # 모의투자
	# host = 'https://api.kiwoom.com'  # 실전투자
	endpoint = '/api/dostk/stkinfo'
	url = host + endpoint

	# 2. header 데이터
	headers = {
		'Content-Type': 'application/json;charset=UTF-8',  # 컨텐츠타입
		'authorization': f'Bearer {token}',  # 접근토큰
		'api-id': 'ka10099',  # TR명
	}

	# 3. 요청 데이터
	params = {
		'mrkt_tp': market,  # 시장구분 0:코스피, 10: 코스닥
	}

	response = try_post(url, headers, params)

	if "error" in response:
		return {"error": f"종목코드 조회 실패: {response['error']}"}

	for stock in response.get('list', []):
		if stock.get('name') == company_name:
			return {stock['name']: stock['code']}

	return {"error": f"'{company_name}'에 해당하는 종목을 찾을 수 없습니다."}


# 기업 목록 조회 함수
def get_stocks_by_keyword(token, keyword, market='0'):
	# 1. 요청할 API URL
	host = 'https://mockapi.kiwoom.com'  # 모의투자
	# host = 'https://api.kiwoom.com'  # 실전투자
	endpoint = '/api/dostk/stkinfo'
	url = host + endpoint

	# 2. header 데이터
	headers = {
		'Content-Type': 'application/json;charset=UTF-8',  # 컨텐츠타입
		'authorization': f'Bearer {token}',  # 접근토큰
		'api-id': 'ka10099',  # TR명
	}
	
	# 3. 요청 데이터
	params = {
		'mrkt_tp': market,  # 시장구분 0:코스피, 10: 코드닥
	}

	response = try_post(url, headers, params)

	if "error" in response:
		return {"error": f"종목 목록 조회 실패: {response['error']}"}

	matches = {
		stock['name']: stock['code']
		for stock in response.get('list', [])
		if keyword in stock.get('name', '')
	}

	return matches or {"error": f"'{keyword}'를 포함하는 종목을 찾을 수 없습니다."}