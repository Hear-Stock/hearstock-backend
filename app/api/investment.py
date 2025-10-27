from fastapi import APIRouter, Query
from app.services.investment_service import get_exchange_rate_info, get_kr_indices, get_world_indices
from app.errors import StockAPIException

router = APIRouter(prefix="/api/investment", tags=["investment"])

# 투자지표 조회 (쿼리 기반)
@router.get("/exchange")
def get_exchange_rate(
	contry: str = Query("", description="국가 입력 예) 미국, 일본")
):
	data = get_exchange_rate_info()

	# 성공 시, 국가 정보 검색
	for i in data:
		if contry in i["cur_nm"]:
			return {
                "국가/통화명": i["cur_nm"],
                "TTB": i["ttb"],
                "TTS": i["tts"],
                "기준율": i["deal_bas_r"]
            }
	
	# 반복문이 끝날 때까지 국가를 찾지 못한 경우
	raise StockAPIException(status_code=404, detail=f"'{contry}'에 대한 환율 정보를 찾을 수 없습니다.")
	
@router.get("/indices")
def get_kr_indece(
	market: str = Query("", description="시장 입력 예) 코스피, 코스닥, 닛케이")
):	
	kr_market = ["코스피", "코스닥", "kospi", "kosdaq"]
	if market in kr_market:
		data = get_kr_indices(market_type=market)
		return data
	else:
		data = get_world_indices()
		for i in data:
			if market in i["indice_name"]:
				return i
		
		raise StockAPIException(status_code=404, detail="입력한 시장 지수 정보가 존재하지 않습니다.")

