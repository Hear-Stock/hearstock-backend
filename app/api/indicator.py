from fastapi import APIRouter
# from app.services.indicator_service import 

router = APIRouter(prefix="/api/indicator", tags=["Indicator"])

# @router.get()
# def get_indicator():
#     return