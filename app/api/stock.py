from fastapi import APIRouter
from pydantic import BaseModel
from app.nlp.gpt_parser import extract_stock_info, extract_price_info, stock_info_parser
from app.services.stock_service import get_stock_chart, get_price, get_overseas_price
from app.api.kiwoomREST import get_kiwoom_stkinfo, get_kiwoom_chart, get_kiwoom_token


router = APIRouter(prefix="/api/stock", tags=["Stock"])

class TextRequest(BaseModel):
	text: str

class ChartDirectRequest(BaseModel):
	stock_code: str
	period: str
	name: str

class StockInfoRequest(BaseModel):
	code: str  # 예: "KRX:005930"
	token: str

@router.post("/price")
def get_price_info(req: TextRequest):
	parsed = extract_price_info(req.text)
	if not parsed:
		return {"error": "GPT 파싱 실패"}

	code = parsed.get("code")
	intent = parsed.get("intent")
	market = parsed.get("market", "KR") 

	if market == "KR":
		code = code.split(".")[0]  
		return get_price(code, intent)

	elif market == "US":
		if intent == "current_price":
			return get_overseas_price(code)
		else:
			return {"error": "해외 종목은 현재가만 지원합니다."}

	else:
		return {"error": f"Unsupported market type: {market}"}

@router.post("/chart")
def get_chart(req: TextRequest):
	parsed = extract_stock_info(req.text)

	if not parsed or "stock_code" not in parsed:
		return {"error": "GPT 파싱 실패"}

	stock_code = parsed["stock_code"]
	period = parsed["period"]
	name = parsed["name"]

	data = get_stock_chart(stock_code, period)

	return {
		"meta": {
			"name": name,
			"code": stock_code,
			"market": "US" if ".KS" not in stock_code and ".KQ" not in stock_code else "KR",
			"intent": "chart",
			"period": period
		},
		"data": data
	}

# 음성이 아닌 버튼으로 차트를 조회할때
@router.post("/chart/direct")
def get_chart_direct(req: ChartDirectRequest):
	stock_code = req.stock_code
	period = req.period
	name = req.name

	if not stock_code or not period:
		return {"error": "필수값 누락"}

	data = get_stock_chart(stock_code, period)

	return {
		"meta": {
			"name": name,
			"code": stock_code,
			"market": "US" if ".KS" not in stock_code and ".KQ" not in stock_code else "KR",
			"intent": "chart",
			"period": period
		},
		"data": data
	}

# 주식 기본 정보(실시간 시세 포함)
@router.post("/stkinfo")
def get_stock_info(req: TextRequest):
	parsed = stock_info_parser(req.text)
	if not parsed:
		return {"error": "GPT 파싱 실패"}

	code = parsed.get("code")
	name = parsed["name"]
	intent = parsed["intent"]
	data = get_kiwoom_stkinfo(token=get_kiwoom_token(), code=code)

	if (intent == ""):	
		return {
			"meta": {
				"name": name,
				"code": code,
				"intent": "",
			},
			"data": data
		}
	else:
		return {
			"meta": {
				"name": name,
				"code": code,
				"intent":intent,
			},
			"data": data[intent]
		}

@router.post("/stkchart")
def get_stock_chart(req: TextRequest):
	parsed = extract_price_info(req.text)
	if not parsed:
		return {"error": "GPT 파싱 실패"}
	
	code = parsed["code"]
	name = parsed["name"]

	code = parsed.get("code")
	data = get_kiwoom_chart(token=get_kiwoom_token(), code=code)

	# JSON 문자열로 변환
	data_json = data.to_json(orient='records', date_format='iso', force_ascii=False)

	return {
		"meta": {
			"name": name,
			"code": code,
			"intent": "chart",
		},
		"data": data_json
	}
