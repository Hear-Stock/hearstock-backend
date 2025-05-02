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
