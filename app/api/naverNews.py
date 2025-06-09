
"""
네이버 검색 api로 검색어의 검색 결과 불러오기
"""
import os
import requests
from dotenv import load_dotenv
from fastapi import APIRouter, Query
from pydantic import BaseModel



router = APIRouter(prefix="/api/news", tags=["News"])

load_dotenv()
def searchNews(query
               ,display = 10
               , start = 1
               , sort = 'sim',
               ):

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

    client_id = os.getenv("NAVER_CLIENT_ID") # naver API ID
    client_secret = os.getenv("NAVER_CLIENT_SECRET") # naver API SECRET KEY

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
        result = []
        # 제목, 링크, 내용, 날짜 출력
        for item in items:
            title = item['title'].replace('<b>', '').replace('</b>', '')  # HTML 태그 제거
            link = item['link']
            description = item['description'].replace('<b>', '').replace('</b>', '')
            pubDate = item['pubDate']

            result.append({
            'title': title,
            'link': link,
            'description': description,
            'pubDate': pubDate
        })

        return result
    else:
        return {"Error:", response.text}
    

@router.get("/searchNews")
def get_news(
		query: str = Query(..., description="검색어 입력")
		, display: str = Query("10", description="검색 개수")
        , start: str = Query("1", description="검색 시작위치")
        , sort: str = Query("sim", description="sim: 정확도순으로 내림차순 정렬(기본값) date: 날짜순으로 내림차순 정렬") ):
	
	return  searchNews(query=query)