import os
import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=api_key)

def extract_intent(text: str):
    prompt = """
    너는 사용자의 자연어 주식 요청 문장을 분석해 아래 JSON을 반환하는 분석기야.

    반환 JSON 형식:
    {
      "name": "종목명",
      "code": "종목코드.시장",
      "market": "KR" 또는 "US",
      "intent": "chart | current_price | high_limit | low_limit | indicator | realtime_chart",
      "period": "1d | 5d | 1mo | 3mo | 6mo | ytd | 1y | 5y | max" (chart일 때만 포함됨)
    }

    기간 표현 매핑:
    - "하루", "오늘" → "1d"
    - "일주일", "1주일", "7일" → "5d"
    - "한 달", "1개월", "30일" → "1mo"
    - "3개월", "3달" → "3mo"
    - "6개월" → "6mo"
    - "올해", "YTD" → "ytd"
    - "1년", "1년치", "작년부터" → "1y"
    - "5년", "5년치" → "5y"
    - "전체", "처음부터", "모든 기간" → "max"
    - 기간 언급이 없으면 기본값 "3mo"

    예시:
    "삼성전자 1년치 주식 차트 보여줘" →
    {
      "name": "삼성전자",
      "code": "005930.KS",
      "market": "KR",
      "intent": "chart",
      "period": "1y"
    }

    "에코프로 현재가 알려줘" →
    {
      "name": "에코프로",
      "code": "086520.KQ",
      "market": "KR",
      "intent": "current_price"
    }

    JSON 외에 아무 설명도 하지 마세요.
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

        # 기본 검증 + period는 선택적 (chart일 때만 있음)
        required_keys = {"name", "code", "intent", "market"}
        if not required_keys.issubset(parsed.keys()):
            return None

        # chart인데 period가 없으면 기본값 적용
        if parsed["intent"] == "chart":
            parsed["period"] = parsed.get("period", "3mo")

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