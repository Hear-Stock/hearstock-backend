import requests
from bs4 import BeautifulSoup
import re
import yfinance as yf

# 숫자 추출 및 소수점 1자리 반올림
def extract_number(text: str) -> str:
    numbers = re.findall(r'\d+\.?\d*', text.replace(',', ''))
    return str(round(float(numbers[0]), 1)) if numbers else "N/A"

# 시가총액 파싱 (조 단위 + 억 단위)
def parse_market_cap(soup) -> float:
    try:
        em = soup.select_one("em#_market_sum")
        if not em:
            return 0

        # 텍스트를 긁고, 콤마 제거하고, 공백 기준으로 분리
        text = em.get_text(separator=' ', strip=True).replace(',', '')

        parts = text.split()
        trillion = 0
        billion = 0

        if len(parts) >= 1:
            trillion_text = parts[0].replace('조', '').strip()
            if trillion_text:
                trillion = int(trillion_text)

        if len(parts) >= 2:
            billion_text = parts[1].strip()
            if billion_text:
                billion = int(billion_text)

        total = (trillion * 1_0000_0000_0000) + (billion * 100_000_000)
        return total
    except Exception as e:
        print("market_cap parsing error:", e)
        return 0

# per_table에서 배당수익률, PER, PBR 가져오기
def get_td_by_th_title(soup, keyword: str) -> str:
    rows = soup.select("table.per_table tr")
    for row in rows:
        th = row.select_one("th")
        td = row.select_one("td")
        if not th or not td:
            continue
        if keyword in th.text:
            return extract_number(td.text)
    return "N/A"

# 외국인 소진율 가져오기
def get_foreign_ownership(soup) -> str:
    try:
        table = soup.find("table", {"summary": "외국인한도주식수 정보"})
        if not table:
            return "N/A"

        row = table.find("tr", class_="strong")
        if not row:
            return "N/A"

        em = row.find("em")
        if em and "%" in em.text:
            return extract_number(em.text)
    except Exception as e:
        print("foreign_ownership error:", e)

    return "N/A"

# 동종업종비교 테이블에서 ROE 가져오기
def get_roe(soup) -> str:
    try:
        table = soup.find("table", {"class": "tb_type1 tb_num", "summary": "동종업종 비교에 관한표이며 종목명에 따라 정보를 제공합니다."})
        if not table:
            return "N/A"
        
        rows = table.select("tr")
        for row in rows:
            th = row.select_one("th")
            tds = row.select("td")
            if th and "ROE(%)" in th.text and tds:
                return extract_number(tds[0].text)
    except Exception as e:
        print("roe error:", e)

    return "N/A"

# 매출액 가져오기 (기업실적분석 테이블)
def get_revenue(soup) -> str:
    try:
        table = soup.find("table", summary="기업실적분석에 관한표이며 주요재무정보를 최근 연간 실적, 분기 실적에 따라 정보를 제공합니다.")
        if not table:
            return "N/A"

        rows = table.select("tr")
        for row in rows:
            th = row.find("th")
            tds = row.find_all("td")
            if th and "매출액" in th.text and tds:
                value = extract_number(tds[2].text)
                if value != "N/A":
                    return str(float(value) * 100_000_000)  # 억 → 원 변환
    except Exception as e:
        print("revenue error:", e)

    return "N/A"

# 전체 통합
def crawl_investment_metrics(stock_code: str) -> dict:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Referer": "https://finance.naver.com/"
    }
    url = f"https://finance.naver.com/item/main.nhn?code={stock_code}"
    res = requests.get(url, headers=headers)
    res.encoding = "UTF-8"
    soup = BeautifulSoup(res.text, "html.parser")

    try:
        corp_name = soup.select_one("div.wrap_company h2").text.strip()

        # 시가총액 파싱 (조/억 단위 변환)
        market_cap = parse_market_cap(soup)

        # 매출액 가져오기
        revenue = get_revenue(soup)

        # psr 계산 (시가총액 / 매출액)
        if market_cap != 0 and revenue != "N/A" and float(revenue) != 0:
            psr = round(float(market_cap) / float(revenue), 2)
        else:
            psr = "N/A"

        # 시가총액 순위
        try:
            table = soup.find("table", summary="시가총액 정보")
            tds = table.find_all("td") if table else []
            market_rank = tds[1].get_text(strip=True) if len(tds) > 1 else None
        except Exception:
            market_rank = None

        # 투자의견 및 목표주가
        try:
            table = soup.find("table", summary="투자의견 정보")
            tds = table.find_all("td") if table else []
            if len(tds) > 0:
                opinion_span = tds[0].find("span", class_="f_up")
                investment_opinion = opinion_span.get_text(strip=True) if opinion_span else None
                em_tags = tds[0].find_all("em")
                target_price = em_tags[-1].get_text(strip=True).replace(",", "") if em_tags else None
            else:
                investment_opinion = None
                target_price = None
        except Exception:
            investment_opinion = None
            target_price = None

        # 동일 업종명
        try:
            a_tag = soup.find("div", class_="section trade_compare").find("a")
            industry_name = a_tag.get_text(strip=True)
        except Exception:
            industry_name = None
        

        # 동일업종 PER, 등락률 정보
        try:
            table = soup.find("table", summary="동일업종 PER 정보")
            tds = table.find_all("td") if table else []
            industry_per = tds[0].get_text(strip=True) if len(tds) > 0 else None
            industry_rate = tds[1].get_text(strip=True) if len(tds) > 1 else None
        except Exception:
            industry_per = None
            industry_rate = None

        return {
            "corp_name": corp_name,
            "market_cap": str(int(market_cap)),
            "market_rank": market_rank,
            "revenue": revenue,
            "psr": psr,
            "per": get_td_by_th_title(soup, "PER"),
            "pbr": get_td_by_th_title(soup, "PBR"),
            "dividend_yield": get_td_by_th_title(soup, "배당수익률"),
            "roe": get_roe(soup),
            "foreign_ownership": get_foreign_ownership(soup),
            "industry_name" : industry_name,
            "opinion": investment_opinion,
            "target_price": target_price,
            "industry_per": industry_per,
            "industry_rate": industry_rate
        }

    except Exception as e:
        return {"error": str(e)}

def get_us_investment_metrics(symbol: str) -> dict:
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info

        return {
            "corp_name": info.get("shortName", symbol),
            "market_cap": str(info.get("marketCap", "N/A")),
            "dividend_yield": str(round(info.get("dividendYield", 0) * 100, 2)) if info.get("dividendYield") else "N/A",
            "per": str(info.get("trailingPE", "N/A")),
            "pbr": str(info.get("priceToBook", "N/A")),
            "roe": str(round(info.get("returnOnEquity", 0) * 100, 2)) if info.get("returnOnEquity") else "N/A",
            "psr": str(info.get("priceToSalesTrailing12Months", "N/A")),
        }
    except Exception as e:
        return {"error": f"yfinance error: {e}"}

def get_investment_metrics(code: str, market: str):
    if market == "KR":
        return crawl_investment_metrics(code)  # 네이버 크롤링
    elif market == "US":
        return get_us_investment_metrics(code)  # yfinance API
    else:
        return {"error": f"Unsupported market: {market}"}
    

# --- 용어 사전 ---
FINANCIAL_TERMS = {
	"PER": "PER은 주가수익비율을 의미하며, 현재 주가를 주당 순이익으로 나눈 값으로 기업의 이익 대비 주가 수준을 나타냅니다. PER이 낮을수록 주가가 저평가되었다고 해석할 수 있습니다.",
	"PBR": "PBR은 주가순자산비율을 의미하며, 현재 주가를 주당 순자산으로 나눈 값으로 기업의 자산 대비 주가 수준을 나타냅니다. PBR이 1보다 낮으면 주가가 저평가되었다고 해석할 수 있습니다.",
	"ROE": "ROE는 자기자본이익률을 의미하며, 기업이 자기자본으로 얼마나 효율적으로 이익을 창출했는지를 나타내는 지표입니다. ROE가 높을수록 수익성이 좋다고 해석할 수 있습니다.",
	"PSR": "PSR은 주가매출비율을 의미하며, 현재 주가를 주당 매출액으로 나눈 값으로 기업의 매출액 대비 주가 수준을 나타냅니다. PSR은 주로 성장하는 기업의 가치를 평가할 때 사용되며, 낮을수록 저평가되었다고 해석할 수 있습니다.",
    "REVENUE": "매출액은 기업이 일정 기간 동안 상품 판매나 서비스 제공을 통해 벌어들인 총액을 의미합니다. 기업의 규모와 성장성을 파악하는 중요한 지표입니다.",
    "DIVIDEND_YIELD": "배당수익률은 현재 주가 대비 연간 배당금의 비율을 나타냅니다. 투자자가 주식 보유를 통해 얻을 수 있는 현금 수익의 정도를 보여줍니다.",
    "FOREIGN_OWNERSHIP": "외국인 소진율은 특정 종목의 발행 주식 총수 중 외국인 투자자가 보유하고 있는 주식의 비율을 나타냅니다. 외국인 투자자의 관심도와 시장의 신뢰도를 파악하는 데 활용될 수 있습니다."
}


# 금융 용어의 정의를 찾아 반환합니다
def get_financial_definition(term: str) -> str:
	term_upper = term.upper()
	definition = FINANCIAL_TERMS.get(term_upper)
	
	if definition:
		return definition
	else:
		return f"죄송합니다, 요청하신 용어 '{term}'에 대한 정보를 찾을 수 없습니다."


# 실행 예시
if __name__ == "__main__":
    result = crawl_investment_metrics("005930")  # 삼성전자
    print(result)
