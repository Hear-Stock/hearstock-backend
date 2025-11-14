import time
import logging
import traceback
import os
from logging.handlers import TimedRotatingFileHandler
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from app.api import stock, indicator, investment, intent, naverNews
from app.errors import add_exception_handlers, StockAPIException

# 로깅 설정
LOG_DIR = "logs"
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# 포매터 생성
formatter = logging.Formatter('%(asctime)s | %(levelname)-8s | %(name)s | [%(filename)s:%(lineno)d] - %(message)s')

# 스트림 핸들러 (콘솔 출력)
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)

# 시간 기반 파일 로테이션 핸들러
# 매일 자정에 새 파일을 생성하고, 최대 30개의 백업 파일을 유지
file_handler = TimedRotatingFileHandler(
    os.path.join(LOG_DIR, 'app.log'), 
    when='midnight', 
    interval=1, 
    backupCount=30,
    encoding='utf-8'
)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

app = FastAPI()

add_exception_handlers(app)

@app.middleware("http")
async def log_requests_and_errors(request: Request, call_next):
    start_time = time.time()
    
    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        
        # 클라이언트 IP, 요청 메소드, 경로, 응답 코드, 처리 시간을 로그로 남김
        log_message = (
            f"client: {request.client.host} - \"{request.method} {request.url.path}\" "
            f"{response.status_code} | process_time: {process_time:.4f}s"
        )
        
        if response.status_code >= 500:
            logger.error(log_message)
        elif response.status_code >= 400:
            logger.warning(log_message)
        else:
            logger.info(log_message)
            
        return response

    except Exception as e:
        process_time = time.time() - start_time
        error_details = {
            "client": request.client.host,
            "method": request.method,
            "path": request.url.path,
            "process_time": f"{process_time:.4f}s",
            "error_type": type(e).__name__,
            "error_message": str(e),
            "traceback": traceback.format_exc()
        }
        logger.error(f"Unhandled exception: {error_details}")
        
        # 클라이언트에게는 간단한 500 에러 메시지를 반환
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal Server Error"},
        )

origins = [
    "http://localhost:7789",
    "http://localhost:3000",
    "https://hearstock-frontend-react-1.vercel.app/webView",
    "https://hearstock-frontend-react-1.vercel.app"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 각 router 등록
app.include_router(stock.router)
app.include_router(intent.router)
app.include_router(indicator.router)
app.include_router(investment.router)
app.include_router(naverNews.router)