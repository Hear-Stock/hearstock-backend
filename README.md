## Fast API 실행

```
uvicorn app.main:app --reload
```

API 실행 페이지: <http://localhost:8000/docs>

## API 성능 테스트
/hearstock-backend 이동 후 터미널에 명령어 실행
```
locust -f locustfile.py
```

🔗 Locust 대시보드 접속
주소로 접속하여 테스트:
👉 http://localhost:8089

 테스트 설정 값 (Locust 웹 UI에서 입력)
 
* Number of users: 100
→ 동시에 접속할 가상 사용자 수

* Spawn rate: 10
→ 초당 생성되는 사용자 수

* Host: http://localhost:8000
→ 테스트 대상 서버 주소 (FastAPI 서버)


## API 사용 현황
1. 키움증권 REST API
- 국내 주식 정보 조회의 핵심 기능을 사용하기 위한 API입니다.
2. 한국 수출입은행
- 환율 정보를 조회하기 위한 API입니다.
3. Yahoo Finance
- 공식적으로 제공하는 라이브러리를 사용해서 해외 주식 정보를 조회에 사용합니다.
4. Naver News API
- 네이버의 공식 검색 API를 통해 뉴스 기사를 검색하고 가져오기 위해 사용됩니다.

## 웹 크롤링 사용
1. 네이버 증권
- <https://finance.naver.com/>
- 네이버 증권 페이지에서 더욱 자세한 투자지표를 조회하기 위해서 사용합니다.
2. Investing
- https://kr.investing.com/indices/major-indices
- 주요 지수 정보를 크롤링하기 위해 사용됩니다.
3. Yahoo Finance (웹 크롤링)
- 자세한 주식 코드를 찾을 때 사용합니다.
- https://finance.yahoo.com/lookup?
 










