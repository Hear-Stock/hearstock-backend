from fastapi import APIRouter, UploadFile, File
from pydantic import BaseModel
import pandas as pd
from app.services.whisper_service import transcribe

router = APIRouter(prefix="/api/whisper", tags=["Whisper"])

# whisper 음성 텍스트 변환
@router.post("/transcribe")
async def handle_transcribe(file: UploadFile):
    text = await transcribe(file)
    return {"text": text}

df = pd.read_csv("stock_list.csv", encoding="cp949")
df = df[['종목명', '종목코드']]
df.columns = ['name', 'code']
df['code'] = df['code'].apply(lambda x: str(x).zfill(6))

class QueryRequest(BaseModel):
    text: str

def find_stock_name(text: str):
    for name in df['name']:
        if name in text:
            return name
    for name in df['name']:
        if name.startswith(text.strip()):
            return name
    return None

def classify_intent(text: str):
    if any(word in text for word in ["차트", "그래프", "흐름"]):
        return "차트 조회"
    elif "주가" in text or "가격" in text:
        return "현재가 조회"
    elif "상한가" in text:
        return "상한가 조회"
    elif "하한가" in text:
        return "하한가 조회"
    else:
        return "기타"

# 텍스트 분석
@router.post("/analyze-text")
def parse_query(request: QueryRequest):
    text = request.text
    entity = find_stock_name(text)
    intent = classify_intent(text)
    code = df[df['name'] == entity]['code'].values[0] if entity else None

    return {
        "entity": entity or "미인식",
        "intent": intent,
        "code": code or "미확인"
    }