import requests
import os
import certifi
from dotenv import load_dotenv
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import json
from app.api import kiwoomREST

load_dotenv()
# 환율 정보 API 키 로드
EXCHANGE_RATE_KEY = os.getenv("EXCHANGE_RATE_KEY")

# 환율 정보 API 사용 (한국수출입은행)
def _fetch_exchange_rate(date_str: str) -> dict:
    url = "https://www.koreaexim.go.kr/site/program/financial/exchangeJSON"
    
    params = {
        'authkey': EXCHANGE_RATE_KEY,
        'searchdate': date_str,
        'data': 'AP01',
    }
    
    try:
        response = requests.get(url, params=params)
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": f"환율 정보 조회 중 오류가 발생했습니다: {e}"}
    except (KeyError, TypeError):
        return {"error": "환율 정보의 형식이 예상과 다릅니다."}
# 오늘 환율이 조회되지 않으면 어제 환율 조회되게 예외 처리
def get_exchange_rate_info() -> dict:
    today = datetime.today()
    today_str = today.strftime('%Y%m%d')
    yesterday = today - timedelta(days=1)
    yesterday_str = yesterday.strftime('%Y%m%d')

    # 오늘 날짜로 먼저 시도
    today_data = _fetch_exchange_rate(today_str)
    if today_data and "error" not in today_data and len(today_data) > 0:
        return today_data
    
    # 오늘 날짜 데이터가 없거나 오류 발생 시 어제 날짜로 시도
    yesterday_data = _fetch_exchange_rate(yesterday_str)
    if yesterday_data and "error" not in yesterday_data and len(yesterday_data) > 0:
        return yesterday_data
    
    # 두 시도 모두 실패
    return {"error": "환율 정보를 가져오는 데 실패했습니다. 오늘 및 어제 날짜의 데이터를 찾을 수 없습니다."}

# 시장 지수 설명
def get_kr_indices(market_type):
	# 업종코드 '001'은 코스피, '101'은 코스닥
	code = ""
	# market_type에 따라 코드 및 시장 이름 설정
	if market_type == "kospi" or market_type == "코스피":
		code = "001"
		market="코스피"
	elif market_type == "kosdaq" or market_type == "코스닥":
		code = "101"
		market="코스닥"
	else:
		# 유효하지 않은 market_type에 대한 오류 반환
		return json.dumps({"error": "유효하지 않은 market_type입니다. 'kospi' 또는 'kosdaq'을 사용하세요."})
	
	# Kiwoom REST API를 통해 시장 지수 정보 가져오기
	indice = kiwoomREST.get_industry_price(kiwoomREST.get_kiwoom_token(), code=code)['all_inds_idex'][0]
	try:
		# 지수 정보 파싱 및 요약
		indice_price = abs(float(indice.get('cur_prc')))
		indice_pred = indice.get('pred_pre')
		indice_change = "하락" if indice.get('pre_sig') == 5 else "상승"
		indice_change_rate = abs(float(indice.get('flu_rt')))
		summary = f"{market} 지수는 {indice_price} 전일 대비 {indice_change_rate}% {indice_change}했습니다."

		# 결과 데이터 구성
		data = {'indice_name': market,
			"지수" : indice_price,
			"등락율" : indice_change_rate,
			"전일대비" : indice_pred,
			"summary": summary}
		
		return data

	except (IndexError, KeyError) as e:
		# 지수 정보 파싱 오류 처리
		market_index_summary = "시장 지수 정보를 가져오는 데 실패했습니다."
		print(f"Error parsing market index: {e}")

	return market_index_summary

# Investing.com에서 주요 해외 지수를 크롤링하여 정보를 반환합니다.
def get_world_indices():
	"""
	Investing.com에서 주요 해외 지수를 크롤링하여 정보를 반환합니다.
	"""
	url = "https://kr.investing.com/indices/major-indices"
	headers = {'User-Agent': 'Mozilla/5.0'}
	response = requests.get(url, headers=headers)
	# BeautifulSoup을 사용하여 HTML 파싱
	soup = BeautifulSoup(response.text, 'lxml')

	try:
		# 지수 테이블 찾기
		table = soup.find('table', class_='datatable-v2_table__93S4Y')
		if not table:
			# 테이블을 찾을 수 없는 경우 오류 반환
			return {"error": "해외 주요 지수 정보를 찾을 수 없습니다."}

		indices_data = []
		# 테이블의 각 행을 순회하며 데이터 추출
		for row in table.select('tbody tr'):
			cols = row.find_all('td')
			if len(cols) < 8:
				continue

			# 각 열에서 필요한 데이터 추출
			index_name = cols[1].get_text(strip=True)
			last_price = cols[2].get_text(strip=True)
			high_price = cols[3].get_text(strip=True)
			low_price = cols[4].get_text(strip=True)
			change = cols[5].get_text(strip=True)
			change_percent = cols[6].get_text(strip=True)

			# 추출된 데이터를 리스트에 추가
			indices_data.append({
				"indice_name": index_name,
				"종가": last_price,
				"고가": high_price,
				"저가": low_price,
				"변동": change,
				"변동%": change_percent
			})

		if not indices_data:
			# 파싱된 데이터가 없는 경우 오류 반환
			return {"error": "해외 주요 지수 데이터를 파싱할 수 없습니다."}

		return indices_data[3:]

	except Exception as e:
		# 크롤링 중 발생한 예외 처리
		return {"error": f"해외 주요 지수 정보를 가져오는 중 오류가 발생했습니다: {e}"}
	

if __name__ == "__main__":
	print(get_exchange_rate_info())