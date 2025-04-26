import json
from pathlib import Path

CORP_CODE_PATH = Path(__file__).resolve().parents[2] / "resources" / "corp_codes.json"

def get_corp_code_by_stock_code(stock_code: str) -> str:
    with open(CORP_CODE_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    for item in data:
        if item["stock_code"] == stock_code:
            return item["corp_code"]
    return None
