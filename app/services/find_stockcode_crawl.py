import requests
from bs4 import BeautifulSoup

def search_ticker_by_name(company_name):
    query = company_name.replace(" ", "+")
    url = f"https://finance.yahoo.com/lookup?s={query}"
    
    headers = {
        "User-Agent": "Mozilla/5.0"
    }
    
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")

    table = soup.find("table")
    if not table:
        return None
    
    rows = table.find_all("tr")[1:]  # Skip header row

    for row in rows:
        cols = row.find_all("td")
        if len(cols) >= 2:
            symbol = cols[0].text.strip()
            return symbol  # 첫 번째 결과 바로 반환
        
    # 검색 목록 # 리스트 형태로 반환 (심볼, 이름)
    # rows = table.find_all("tr")[1:]  # Skip header row
    # results = []
    # for row in rows:
    #     cols = row.find_all("td")
    #     if len(cols) >= 2:
    #         symbol = cols[0].text.strip()
    #         name = cols[1].text.strip()
    #         results.append((symbol, name))
    
    # return results  

    return None  # 유효한 결과가 없을 경우

    

if __name__ == "__main__":
    # 사용 예시
    result = search_ticker_by_name("microsoft")
    # for symbol, name in result:
    #     print(f"{name} -> {symbol}")

    print(result)
