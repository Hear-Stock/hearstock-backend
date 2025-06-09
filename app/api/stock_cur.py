from fastapi import APIRouter, Query
from pydantic import BaseModel
from app.api.kiwoomREST import get_kiwoom_token, get_kiwoom_stkinfo, get_kiwoom_chart, get_stock_code, get_stocks_by_keyword
from app.services.industry_service import get_industry_per
from app.nlp.gpt_parser import extract_price_info

router = APIRouter(prefix="/api/stk", tags=["StockCurrent"])



# 주식 실시간 정보
@router.get("/curPrice")
def get_stock_info(code: str = Query(..., description="종목 코드 (예: 005930, 000660 등)"),
				   intent: str = Query(None, description="고가, 시가, 저가")):

	stk_info = get_kiwoom_stkinfo(token=get_kiwoom_token(), code=code)
	# 실시간 가격 부분만 추출
	cur_info = {
		"종목코드": stk_info["stk_cd"],
		"종목명": stk_info["stk_nm"],
		"고가": stk_info["high_pric"],
		"시가": stk_info["open_pric"],
		"저가": stk_info["low_pric"],
		"현재가": stk_info["cur_prc"],
		"등락율": stk_info["flu_rt"],
		"거래량": stk_info["trde_qty"]
	}


	if (intent == None):
		return cur_info
	else:
		return {
		"종목코드": stk_info["stk_cd"],
		"종목명": stk_info["stk_nm"],
		intent: cur_info[intent]
	}


@router.get("/stkchart")
def get_stock_chart(code: str = Query(..., description="종목 코드 (예: 005930, 000660 등)")):

	data = get_kiwoom_chart(token=get_kiwoom_token(), code=code)
	
	result = data.to_dict(orient='records')

	return result


@router.get("/metric")
def get_stock_metrics(
		code: str = Query(..., description="종목 코드 (예: 005930, 000660 등)")
		, ):
	stock_data = get_kiwoom_stkinfo(token=get_kiwoom_token(), code=code)
	industry_data = get_industry_per(code)

	# stock_data에 업종 데이터 병합
	stock_data["industry_per"] = industry_data.get("per")
	stock_data["industry_change_rate"] = industry_data.get("change_rate")

	# 필요한 투자지표만 추출
	filtered_data = {
		"mac": stock_data.get("mac"),  # 시가총액
		"upl_pric": stock_data.get("upl_pric"),  # 상한가
		"lst_pric": stock_data.get("lst_pric"),	# 하한가
		"sale_amt": stock_data.get("sale_amt"),	# 매출액
		"bus_pro": stock_data.get("bus_pro"), # 영업이익
		"cup_nga": stock_data.get("cup_nga"), # 당기순이익
		"per": stock_data.get("per"),
		"eps": stock_data.get("eps"),
		"roe": stock_data.get("roe"),
		"pbr": stock_data.get("pbr"),
		"ev": stock_data.get("ev"),
		"bps": stock_data.get("bps"),
		"industry_per": stock_data.get("industry_per"),
		"industry_change_rate": stock_data.get("industry_change_rate")
	}

	return filtered_data


@router.get("/findstk")
def get_name_and_code(
		keyword: str = Query(..., description="키워드 입력 예) 삼성, 현대")
		, ):
	
	result = get_stocks_by_keyword(token=get_kiwoom_token(), keyword=keyword)

	return result