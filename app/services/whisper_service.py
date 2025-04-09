import io
import whisper
import os
from fastapi import UploadFile

model = whisper.load_model("base") 

async def transcribe(file: UploadFile) -> str:
    contents = await file.read()
    
    temp_filename = f"temp_{file.filename}" # 임시로 파일 저장 (Whisper는 파일 경로 필요)
    with open(temp_filename, "wb") as f:
        f.write(contents)

    result = model.transcribe(temp_filename) # whisper로 텍스트 변환

    os.remove(temp_filename)

    return result["text"]
