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

