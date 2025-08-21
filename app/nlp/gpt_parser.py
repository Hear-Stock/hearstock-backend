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
      "intent": "chart | current_price | high_limit | low_limit | indicator | realtime_chart | exchange_rate | market_index",
      "period": "1d | 5d | 1mo | 3mo | 6mo | ytd | 1y | 5y | max" (chart일 때만 포함됨),
      "indicator_type": "PER | PBR | PSR | ROE | dividend_yield | market_cap | revenue | target_price | opinion | foreign_ownership" (intent가 'indicator'일 때, 사용자가 특정 지표를 언급한 경우에만 포함),
      "country": "국가명" (intent가 'exchange_rate'일 때만 포함),
      "market_name": "시장 지수명" (intent가 'market_index'일 때만 포함)
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

    보조지표(indicator) 종류 매핑:
    - "PER", "주가수익비율" → "per"
    - "PBR", "주가순자산비율" → "pbr"
    - "PSR", "주가매출비율" → "psr"
    - "ROE", "자기자본이익률" → "roe"
    - "배당수익률" → "dividend_yield"
    - "시가총액" → "market_cap"
    - "매출액" → "revenue"
    - "목표주가" → "target_price"
    - "투자의견" → "opinion"
    - "외국인소진율" → "foreign_ownership"
    - 사용자가 "보조지표 알려줘" 처럼 특정 지표를 언급하지 않으면 "indicator_type"은 null 또는 미포함.

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

    "카카오 PER 알려줘" →
    {
      "name": "카카오",
      "code": "035720.KS",
      "market": "KR",
      "intent": "indicator",
      "indicator_type": "per"
    }

    "네이버 투자지표 보여줘" →
    {
        "name": "네이버",
        "code": "035420.KS",
        "market": "KR",
        "intent": "indicator"
    }

    "미국 달러 환율 알려줘" →
    {
      "intent": "exchange_rate",
      "country": "미국"
    }

    "코스피 지수 어때?" →
    {
      "intent": "market_index",
      "market_name": "코스피"
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
        # 모델의 응답에서 JSON 부분만 추출
        json_start = result.find('{')
        json_end = result.rfind('}') + 1
        if json_start == -1 or json_end == 0:
            return None # 응답에서 JSON 객체를 찾지 못한 경우
            
        json_string = result[json_start:json_end]
        parsed = json.loads(json_string)

        # chart인데 period가 없으면 기본값 3개월 적용
        if parsed.get("intent") == "chart":
            parsed["period"] = parsed.get("period", "3mo")

        # indicator일 때는 prefix 제거
        if parsed.get("intent") == "indicator":
            if "code" in parsed:
                parsed["code"] = parsed["code"].split('.')[0]

        # 해외 주식이면 prefix 제거
        if parsed.get("market") == "US" and "." in parsed.get("code", ""):
            if "code" in parsed:
                parsed["code"] = parsed["code"].split('.')[0]

        return parsed
    except json.JSONDecodeError:
        return None
