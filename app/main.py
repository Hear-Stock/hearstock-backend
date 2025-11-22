import time
import logging
import logging.config
import traceback
import os
import uuid
from pythonjsonlogger import jsonlogger
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from app.api import stock, indicator, investment, intent, naverNews
from app.errors import add_exception_handlers, StockAPIException

# 로그 디렉토리 설정
LOG_DIR = "logs"
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

# 구조화된 로깅 설정 (JSON 형식)
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {
            "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
            "format": "%(asctime)s %(name)s %(levelname)s %(message)s %(filename)s %(lineno)d",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "json",
            "level": logging.INFO,
        },
        "file": {
            "class": "logging.handlers.TimedRotatingFileHandler",
            "filename": os.path.join(LOG_DIR, "app.log"),
            "when": "midnight",
            "interval": 1,
            "backupCount": 30,
            "formatter": "json",
            "level": logging.INFO,
            "encoding": "utf-8",
        },
    },
    "loggers": {
        "": {
            "handlers": ["console", "file"],
            "level": logging.INFO,
        },
        "uvicorn.access": {
            "handlers": [], # Uvicorn 접근 로그 비활성화
            "level": logging.INFO,
            "propagate": False,
        },
        "uvicorn.error": {
            "handlers": ["console", "file"],
            "level": logging.ERROR,
            "propagate": False,
        },
    },
}

logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger(__name__)

app = FastAPI()

add_exception_handlers(app)

@app.middleware("http")
async def log_requests_and_errors(request: Request, call_next):
    request_id = str(uuid.uuid4())
    start_time = time.time()
    
    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        
        log_details = {
            "request_id": request_id,
            "client": request.client.host,
            "method": request.method,
            "url": str(request.url),  # .path 대신 전체 URL을 기록하도록 변경
            "status_code": response.status_code,
            "process_time_seconds": f"{process_time:.4f}",
        }

        if response.status_code >= 500:
            logger.error("Request finished with server error", extra=log_details)
        elif response.status_code >= 400:
            logger.warning("Request finished with client error", extra=log_details)
        else:
            logger.info("Request finished successfully", extra=log_details)
            
        return response

    except Exception as e:
        process_time = time.time() - start_time
        error_details = {
            "request_id": request_id,
            "client": request.client.host,
            "method": request.method,
            "url": str(request.url),  # .path 대신 전체 URL을 기록하도록 변경
            "process_time_seconds": f"{process_time:.4f}",
            "error_type": type(e).__name__,
            "error_message": str(e),
            "traceback": traceback.format_exc().splitlines(),
        }
        logger.error("Unhandled exception", extra=error_details)
        
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal Server Error", "request_id": request_id},
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