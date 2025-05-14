import requests

"""
네이버 검색 api로 검색어의 검색 결과 불러오기
"""

def searchNews(query="삼성전자", display = 10, start = 1, sort = 'sim'):
    base_url = "https://openapi.naver.com/v1/search/news.json"
    client_id = 'id'
    client_secret = "secret"

    # 쿼리 파라미터 딕셔너리
    params = {
        'query': query, # 검색어
        'display': display, # 결과 개수
        'start': start, # 검색 시작 위치
        'sort': sort # sim: 정확도순으로 내림차순 정렬(기본값) date: 날짜순으로 내림차순 정렬
    }

    client_id = "qMJH0HY24H3uy6fO5lA7" # naver API ID
    client_secret = "GwEC7cnhH9" # naver API SECRET KEY

    # 헤더 설정
    headers = {
        'X-Naver-Client-Id': client_id,
        'X-Naver-Client-Secret': client_secret
    }

    # GET 요청
    response = requests.get(base_url, headers=headers, params=params)

    # 응답 코드 확인
    print(response.status_code)

    # 응답 데이터(JSON)
    if response.status_code == 200:
        json = response.json()
        items = json['items']
        # 제목, 링크, 내용, 날짜 출력력
        for item in items:
            title = item['title'].replace('<b>', '').replace('</b>', '')  # HTML 태그 제거
            link = item['link']
            description = item['description'].replace('<b>', '').replace('</b>', '')
            pubDate = item['pubDate']

            print(f"Title: {title}")
            print(f"Link: {link}")
            print(f"Description: {description}")
            print(f"Published Date: {pubDate}")
            print()
    else:
        print("Error:", response.text)

if __name__ == "__main__":
    searchNews()