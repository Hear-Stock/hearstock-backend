import requests
from bs4 import BeautifulSoup
import re

def extract_number(text: str) -> str:
    numbers = re.findall(r'\d+\.?\d*', text.replace(',', ''))
    return str(round(float(numbers[0]), 1)) if numbers else "N/A"

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

def crawl_investment_metrics(stock_code: str) -> dict:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Referer": "https://finance.naver.com/"
    }
    url = f"https://finance.naver.com/item/main.nhn?code={stock_code}"
    res = requests.get(url, headers=headers)
    res.encoding = "euc-kr"
    soup = BeautifulSoup(res.text, "html.parser")

    try:
        corp_name = soup.select_one("div.wrap_company h2").text.strip()
        market_cap = extract_number(soup.select_one("em#_market_sum").text)

        return {
            "corp_name": corp_name,
            "market_cap": market_cap,
            "dividend_yield": get_td_by_th_title(soup, "배당수익률"),
            "per": get_td_by_th_title(soup, "PER"),
            "pbr": get_td_by_th_title(soup, "PBR"),
            "roe": "N/A",
            "psr": "N/A",
            "foreign_ownership": get_foreign_ownership(soup)
        }
    except Exception as e:
        return {"error": str(e)}
