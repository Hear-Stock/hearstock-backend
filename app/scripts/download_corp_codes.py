import zipfile
import requests
import xml.etree.ElementTree as ET
import json
from pathlib import Path
from app.config import DART_API_KEY

def download_and_extract_corp_codes():
    url = f"https://opendart.fss.or.kr/api/corpCode.xml?crtfc_key={DART_API_KEY}"
    response = requests.get(url)

    zip_path = Path("corp_code.zip")
    with open(zip_path, "wb") as f:
        f.write(response.content)

    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall(".")

    tree = ET.parse("CORPCODE.xml")
    root = tree.getroot()

    corp_list = []
    for corp in root.findall("list"):
        corp_code = corp.findtext("corp_code")
        corp_name = corp.findtext("corp_name")
        stock_code = corp.findtext("stock_code")
        if stock_code:
            corp_list.append({
                "corp_code": corp_code,
                "corp_name": corp_name,
                "stock_code": stock_code
            })

    resources_path = Path("resources")
    resources_path.mkdir(exist_ok=True)

    with open(resources_path / "corp_codes.json", "w", encoding="utf-8") as f:
        json.dump(corp_list, f, ensure_ascii=False, indent=2)

    print(f"✅ corp_codes.json 생성 완료! 총 {len(corp_list)}개 기업")

if __name__ == "__main__":
    download_and_extract_corp_codes()
