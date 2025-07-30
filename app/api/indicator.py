from fastapi import APIRouter, Query
from app.services.indicator_service import get_investment_metrics, get_financial_definition, extract_number

router = APIRouter(prefix="/api/indicator", tags=["Indicator"])

# 투자지표 조회 (쿼리 기반)
@router.get("/")
def get_investment_info(
	code: str = Query(..., description="종목 코드 (예: 005930, TSLA 등)"),
	market: str = Query("KR", description="시장 구분 (KR | US)")
):
	data = get_investment_metrics(code, market)
	if "error" in data:
		return {"error": data["error"]}
	return data

# 특정 지표 설명 조회 (쿼리 기반)
@router.get("/explain")
def explain_metric(
	code: str = Query(..., description="종목 코드"),
	market: str = Query("KR", description="시장"),
	metric: str = Query(..., description="지표명 (예: PER, PBR, ROE 등)")
):
	data = get_investment_metrics(code, market)

	if "error" in data:
		return {"text": f"해당 종목의 투자지표를 불러올 수 없습니다. ({data['error']})"}
	
	metric_upper = metric.upper()
	# 값 할당
	value_str = data.get(metric.lower())
	industry_per_str = data.get("industry_per")
	industry_rate_str = data.get("industry_rate")
	corp_name = data.get("corp_name", "해당 종목")

	if value_str is None or value_str == "N/A":
		return {"text": f"{metric} 지표는 제공되지 않거나 유효한 값을 찾을 수 없습니다."}

	summary_parts = []
	summary_parts.append(f"{corp_name}의 {metric_upper} 값은 {value_str}입니다.")

	# 단위 제거
	def sanitize_float_string(s):
		if isinstance(s, str):
			if not s or s == "N/A":
				return None
			return s.replace(",", "").replace("%", "").replace("배", "").strip()
		return s

	try:
		value = float(sanitize_float_string(value_str))
		industry_per = float(sanitize_float_string(industry_per_str)) if industry_per_str and industry_per_str != "N/A" else None
		industry_rate = float(sanitize_float_string(industry_rate_str)) if industry_rate_str and industry_rate_str != "N/A" else None
		print(f"value_str: {value_str}, industry_per_str: {industry_per_str}, industry_rate_str: {industry_rate_str}")

		if metric_upper == "PER":
			if industry_per is not None and industry_rate is not None:
				summary_parts.append(f"동일 업종의 평균 PER은 {industry_per}이며, 등락률은 {industry_rate}%입니다.")
				if value < industry_per:
					summary_parts.append(f"이는 동일 업종 평균보다 낮은 수준으로, 상대적으로 저평가되어 있을 가능성이 있습니다.")
				elif value > industry_per:
					summary_parts.append(f"이는 동일 업종 평균보다 높은 수준으로, 상대적으로 고평가되어 있을 가능성이 있습니다.")
				else:
					summary_parts.append(f"이는 동일 업종 평균과 유사한 수준입니다.")
			else:
				summary_parts.append(f"현재 산업 평균 PER과의 비교 정보는 제공되지 않습니다.")
		# 이 밑으로는 비교 없이 일반적으로 평가함
		elif metric_upper == "PBR":
			if value < 1.0:
				summary_parts.append(f"PBR이 1보다 낮으므로, 기업의 자산 가치에 비해 주가가 저평가되어 있다고 볼 수 있습니다.")
			elif value > 1.0:
				summary_parts.append(f"PBR이 1보다 높으므로, 기업의 자산 가치에 비해 주가가 고평가되어 있다고 볼 수 있습니다.")
			else:
				summary_parts.append(f"PBR이 1과 유사하므로, 기업의 자산 가치와 주가가 비슷한 수준입니다.")
		elif metric_upper == "ROE":
			if value > 10.0: # 일반적인 좋은 ROE 기준
				summary_parts.append(f"ROE가 10보다 높은 {value}%로 높은 수준이므로, 기업이 자기자본을 효율적으로 사용하여 이익을 창출하고 있음을 나타냅니다.")
			else:
				summary_parts.append(f"ROE가 10보다 낮은 {value}%이므로, 기업의 자기자본 이익 창출 효율성을 추가적으로 분석해 볼 필요가 있습니다.")
		elif metric_upper == "PSR":
			if value < 1.0: # 일반적인 좋은 PSR 기준 (성장주에 유용)
				summary_parts.append(f"PSR이 1.0보다 낮은 {value}로 낮은 수준이므로, 매출액 대비 주가가 저평가되어 있을 가능성이 있습니다. 특히 성장주 분석에 유용합니다.")
			else:
				summary_parts.append(f"PSR이 1.0보다 높은 {value}이므로, 매출액 대비 주가 수준을 추가적으로 분석해 볼 필요가 있습니다.")

	except ValueError:
		summary_parts.append(f"숫자로 변환할 수 없는 값이 있습니다.")
	except Exception as e:
		summary_parts.append(f"상세 분석 중 오류가 발생했습니다: {e}")


	return {"metric": metric, "summary": " ".join(summary_parts)}

# 금융 용어 정의
@router.get("/definition")
def definition_metirc(
	metric: str = Query(..., description="지표명 (예: PER, PBR, ROE 등)")):
	definition = get_financial_definition(metric)
	return {"metric" : metric, "definition": definition}