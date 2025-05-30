import os
import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=api_key)

def extract_intent(text: str):
    prompt = """
    너는 사용자의 자연어 주식 요청 문장을 분석해 아래 intent 중 하나를 분류하는 분류기야.

    아래 intent 중 하나로 분류해서, 종목명(name), 종목 코드(code), 시장(market), 의도(intent)를 JSON으로 반환하세요:

    - intent 종류:
    - chart: "차트", "캔들", "흐름", "그래프" 등 주가 흐름 요청
    - current_price: 현재가 요청 ("얼마", "시세", "현재가" 등)
    - high_limit: 상한가 요청
    - low_limit: 하한가 요청
    - indicator: 투자지표 요청 (PER, PBR, ROE 등)

    기준:
    - "차트", "흐름", "캔들" → chart
    - "현재가", "얼마", "시세" → current_price
    - "PER", "PBR", "ROE", "투자지표" → indicator
    - "상한가", "하한가" 명시 → 해당 intent

    예시:
    "삼성전자 차트 알려줘" →
    {
        "name": "삼성전자",
        "code": "005930",
        "intent": "chart",
        "market": "KR"
    }

    "테슬라 PER 알려줘" →
    {
        "name": "테슬라",
        "code": "TSLA",
        "intent": "indicator",
        "market": "US"
    }

    반드시 JSON만 출력하고, 설명은 생략하세요.
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
