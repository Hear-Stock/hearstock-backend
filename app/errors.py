from fastapi import Request
from fastapi.responses import JSONResponse

class StockAPIException(Exception):
    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail

def add_exception_handlers(app):
    @app.exception_handler(StockAPIException)
    async def stock_api_exception_handler(request: Request, exc: StockAPIException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
        )
