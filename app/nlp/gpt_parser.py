import os
import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=api_key)
def extract_stock_info(text: str):
    prompt = """
    입력 문장에서 한국 주식 종목명과 조회 기간을 추출해서 아래 형식의 JSON으로 변환하세요:
    {
    "name": "삼성전자",
    "period": "3mo",
    "stock_code": "005930.KS"
    }

    반드시 종목코드는 야후 파이낸스에 맞게 한국 종목은 .KS 또는 .KQ가 붙도록 하세요.
    JSON 외에는 아무 설명도 출력하지 마세요.
    """

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": text}
        ]
    )

    result = response.choices[0].message.content.strip()

    try:
        return json.loads(result)
    except json.JSONDecodeError:
        return None
    
def extract_price_info(text: str):
    prompt = """
    다음 문장에서 주식 종목명과 사용자의 의도, 시장을 JSON 형식으로 반환하세요.

    - intent는 다음 중 하나: current_price, high_limit, low_limit, indicator
    - code는 종목 코드 (예: 삼성전자 → 005930, 테슬라 → TSLA)
    - market은 "KR" (한국) 또는 "US" (미국)

    예시:
    "삼성전자 상한가 알려줘" → {
    "name": "삼성전자",
    "code": "005930",
    "intent": "high_limit",
    "market": "KR"
    }

    "애플 투자지표 알려줘" → {
    "name": "애플",
    "code": "AAPL",
    "intent": "indicator",
    "market": "US"
    }

    JSON 외에 아무 설명도 출력하지 마세요.
    """

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": text}
        ]
    )

    result = response.choices[0].message.content.strip()
    try:
        parsed = json.loads(result)
        if not all(k in parsed for k in ("name", "code", "intent")):
            return None
        return parsed
    except json.JSONDecodeError:
        return None
    

def extract_price_info(text: str):
    prompt = """
    다음 문장에서 주식 종목명과 사용자의 의도, 시장을 JSON 형식으로 반환하세요.

    - intent는 다음 중 하나: current_price, high_limit, low_limit, indicator
    - code는 종목 코드 (예: 삼성전자 → 005930, 테슬라 → TSLA)
    - market은 "KR" (한국) 또는 "US" (미국)

    예시:
    "삼성전자 상한가 알려줘" → {
    "name": "삼성전자",
    "code": "005930",
    "intent": "high_limit",
    "market": "KR"
    }

    "애플 투자지표 알려줘" → {
    "name": "애플",
    "code": "AAPL",
    "intent": "indicator",
    "market": "US"
    }

    JSON 외에 아무 설명도 출력하지 마세요.
    """

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": text}
        ]
    )

    result = response.choices[0].message.content.strip()
    try:
        parsed = json.loads(result)
        if not all(k in parsed for k in ("name", "code", "intent")):
            return None
        return parsed
    except json.JSONDecodeError:
        return None


def stock_info_parser(text: str):
    prompt = """
    

    다음 문장에서 주식 종목명과 사용자의 의도, 시장을 JSON 형식으로 반환하세요.
    intent를 찾을 수 없다면 intent : "" 으로 설정
    - intent는 다음 중 하나: stock_info = {
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
    - code는 종목 코드 (예: 삼성전자 → 005930, sk하이닉스 → 000660)
    - market은 코스피, 코스닥

    예시:
    "삼성전자 상한가 알려줘" → {
    "name": "삼성전자",
    "code": "005930",
    "intent": "upl_pric",
    "market": "코스피"
    }

    예시:
    "sk하이닉스 주식 정보 알려줘" → {
    "name": "SK하이닉스",
    "code": "000660",
    "intent": "",
    "market": "코스피"
    }

    JSON 외에 아무 설명도 출력하지 마세요.
    """

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": text}
        ]
    )

    result = response.choices[0].message.content.strip()
    try:
        parsed = json.loads(result)
        if not all(k in parsed for k in ("name", "code", "intent")):
            return None
        return parsed
    except json.JSONDecodeError:
        return None