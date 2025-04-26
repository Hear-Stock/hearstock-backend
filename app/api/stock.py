from fastapi import APIRouter, Query
from datetime import datetime, timedelta
from app.services.stock_real_service import (
    load_stock_codes,
    fetch_minute_data,
    resample_to_10min,
    insert_to_postgresql
)

router = APIRouter(prefix="/api/stock", tags=["Stock"])

@router.post("/crawl-single")
def crawl_one_stock(
    code: str = Query(...),
    start_date: str = Query(...),
    end_date: str = Query(...)
):
    try:
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        result = []

        curr = start
        total_count = 0
        while curr <= end:
            df = fetch_minute_data(code, curr)
            if not df.empty:
                df10 = resample_to_10min(df)
                insert_to_postgresql(df10, code)
                total_count += len(df10)
            curr += timedelta(days=1)

        return {
            "code": code,
            "saved": total_count,
            "start": start_date,
            "end": end_date
        }

    except Exception as e:
        return {"error": str(e)}
