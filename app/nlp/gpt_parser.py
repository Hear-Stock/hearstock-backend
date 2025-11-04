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
    - 사용자가 "보조지표 알려줘"처럼 특정 지표를 언급하지 않으면 indicator_type은 null 또는 미포함.

    추가 규칙:
    - "realtime_chart"는 intent의 한 종류이며, period가 아니다.
    - 사용자가 "주식 보여줘", "차트 보여줘", "그래프", "흐름", "추이" 등의 시각적 표현을 사용하면 intent="chart"로 분류.
    - 단, 사용자가 기간을 언급하지 않았다면 intent="realtime_chart"로 분류해야 한다.
    - "현재가", "가격", "얼마", "시세" 등 직접적인 가격 문의 표현은 intent="current_price"로 분류.

    예시:
    "삼성전자 3개월치 주식 보여줘" →
    {
      "name": "삼성전자",
      "code": "005930.KS",
      "market": "KR",
      "intent": "chart",
      "period": "3mo"
    }

    "삼성전자 주식 보여줘" →
    {
      "name": "삼성전자",
      "code": "005930.KS",
      "market": "KR",
      "intent": "realtime_chart"
    }

    주의사항:
    - 사용자가 "하루", "3개월", "1년" 등 기간을 직접 말하지 않았다면 절대 "period" 값을 생성하지 마라.

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
        # JSON만 추출
        json_start = result.find('{')
        json_end = result.rfind('}') + 1
        if json_start == -1 or json_end == 0:
            return None

        parsed = json.loads(result[json_start:json_end])

        # period=realtime_chart로 반환한 경우 보정
        if parsed.get("intent") == "chart" and parsed.get("period") == "realtime_chart":
            parsed["intent"] = "realtime_chart"
            parsed.pop("period", None)

        # indicator일 때 code 접미사 제거
        if parsed.get("intent") == "indicator" and "code" in parsed:
            parsed["code"] = parsed["code"].split('.')[0]

        # 해외 주식이면 접미사 제거
        if parsed.get("market") == "US" and "." in parsed.get("code", ""):
            parsed["code"] = parsed["code"].split('.')[0]

        return parsed

    except json.JSONDecodeError:
        return None
