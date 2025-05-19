import os
import redis
import json
import numpy as np
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, Float, String, DateTime
from sqlalchemy.orm import sessionmaker
# from app.config import DB_URL
from app.api.kiwoomAPI import *
from app.data.getCodes import getKospiCodes
from dotenv import load_dotenv


load_dotenv()
# REDIS
REDIS_HOST = os.getenv("REDIS_HOST")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_DB = int(os.getenv("REDIS_DB", 0))
# Redis 연결
redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, decode_responses=True)
# MYSQL 연결
DB_URL = os.getenv("DB_URL")
engine = create_engine(DB_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# JSON 직렬화를 위한 커스텀 인코더
class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (np.integer, np.floating)):
            return int(obj) if isinstance(obj, np.integer) else float(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

def createTable(table_name):
    # 테이블 정의
    metadata = MetaData()
    ohlcv_table = Table(
        table_name, metadata,
        Column('id', Integer, primary_key=True, autoincrement=True),
        Column('code', String(10)),
        Column('open', Float),
        Column('close', Float),
        Column('high', Float),
        Column('low', Float),
        Column('chg_rate', Float),
        Column('volume', Integer),
        Column('timestamp', DateTime)
    )

    # 테이블 생성
    metadata.create_all(bind=engine)
    return ohlcv_table

def saveCompanyCodes(kiwoom, n): # 1회용
    # 테이블 정의
    metadata = MetaData()
    etf = Table(
        "etf", metadata,
        Column('id', Integer, primary_key=True, autoincrement=True),
        Column('code', String(10)),
        Column('name', String(50))
    )

    codes = getCode(kiwoom, n)
    for code in codes:
        name = kiwoom.GetMasterCodeName(code)
        data = {'code': code, 'name': name}
        print(code, name)
        # 테이블 생성
        metadata.create_all(bind=engine)
        save_ohlcv(etf, data)

# 단일 레코드 저장 함수
def save_ohlcv(ohlcv_table, ohlcv_data: dict):
    with engine.connect() as conn:
        with conn.begin():  # Transaction context manager
            insert_stmt = ohlcv_table.insert().values(**ohlcv_data)
            conn.execute(insert_stmt)

# 대량 레코드 저장 함수
def save_ohlcv_bulk(ohlcv_table, ohlcv_data_list: list):
    with engine.connect() as conn:
        with conn.begin():  # Transaction context manager for automatic commit
            conn.execute(ohlcv_table.insert(), ohlcv_data_list)

# 단일 레코드 삽입 함수
def update_ohlcv(ohlcv_table, ohlcv_data: dict):
    with engine.connect() as conn:
        with conn.begin():  # Transaction context manager
            update_stmt = (
                ohlcv_table.update()
                .where(ohlcv_table.c.id == 1)
                .values(**ohlcv_data)
            )
            conn.execute(update_stmt)

def update_ohlcv_bulk(ohlcv_table, ohlcv_data_list: list):
    with engine.connect() as conn:
        with conn.begin():
            for data in ohlcv_data_list:
                # 먼저 기존 데이터 존재 여부 확인
                select_stmt = (
                    ohlcv_table.select()
                    .where(ohlcv_table.c.code == data['code'])
                    .where(ohlcv_table.c.timestamp == data['timestamp'])
                )
                result = conn.execute(select_stmt).fetchone()

                if result:
                    # 기존 row가 있을 경우 update
                    update_stmt = (
                        ohlcv_table.update()
                        .where(ohlcv_table.c.id == result.id)  # id로 update 보장
                        .values(**data)
                    )
                    conn.execute(update_stmt)
                else:
                    # 없으면 insert
                    insert_stmt = ohlcv_table.insert().values(**data)
                    conn.execute(insert_stmt)


# OHLCV 데이터 요청 및 저장 함수
def save_table(kiwoom, table_name, code, date=""):
    ohlcv_table = createTable(table_name)
    df_filtered = request_ohlcv(kiwoom, code, date)
    df_filtered['code'] = code
    # DataFrame을 dict 리스트로 변환
    ohlcv_data_list = df_filtered[['code', 'open', 'close', 'high', 'low', 'chg_rate', 'volume', 'timestamp']].to_dict('records')

    # 데이터베이스에 저장 (대량 삽입)
    if ohlcv_data_list:
        update_ohlcv_bulk(ohlcv_table, ohlcv_data_list)
        print(f"{table_name} 종목의 데이터 {len(ohlcv_data_list)}개가 {table_name} 테이블에 저장되었습니다.")
    else:
        print("저장할 데이터가 없습니다.")

    return df_filtered

# Redis에서 OHLCV 데이터 캐싱
def cache_ohlcv_data(code, ohlcv_data_list: list):
    cache_key = f"ohlcv:{code}"
    # JSON으로 직렬화하여 Redis에 저장 (24시간 TTL)
    redis_client.setex(cache_key, 86400, json.dumps(ohlcv_data_list))

# Redis에서 OHLCV 데이터 조회
def get_cached_data(code):
    cache_key = f"ohlcv:{code}"
    cached_data = redis_client.get(cache_key)
    if cached_data:
        return json.loads(cached_data)
    return None

def insert_colmns(kiwoom, table_name, code):
    ohlcv_table = createTable(table_name)
    df = kiwoom.block_request("opt10001",
                              종목코드=code,
                              output="주식기본정보",
                              next=0)
    # 컬럼을 숫자로 변환
    numeric_columns = ['기준가', '시가', '고가', '저가', '현재가', '등락율', '거래량']
    df[numeric_columns] = df[numeric_columns].apply(pd.to_numeric, errors='coerce')

    ohlcv_data_list ={
        'code' : code,
        'open' : abs(df['시가'][0]),  # 장 시작가
        'close': abs(df['현재가'][0]), # 현재가
        'high': abs(df['고가'][0]),   # 오늘 상한가
        'low': abs(df['저가'][0]),    # 오늘 하한가
        'chg_rate': df['등락율'][0],  # 등락율
        'volume': df['거래량'][0],    # 오늘 거래량
        'timestamp' : datetime.now().replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
    }

    if ohlcv_data_list:
        update_ohlcv(ohlcv_table, ohlcv_data_list)
        # Redis에 실시간 데이터 저장
        redis_client.setex(f"ohlcv:{code}", 600, json.dumps(ohlcv_data_list, cls=CustomJSONEncoder))
        print(f"{table_name} 종목의 데이터 {len(ohlcv_data_list)}개가 {table_name} 테이블에 저장되었습니다.")
    else:
        print("저장할 데이터가 없습니다.")


if __name__ == "__main__":
    kiwoom = Kiwoom()
    kiwoom.CommConnect(block=True)
    # code = '005930'
    # table_name = kiwoom.GetMasterCodeName(code)
    date = ""  # 기준일자 (빈 문자열로 최신 데이터 요청)

    # 시가총액상위 종목 가져오기
    dict = getKospiCodes("../data/kospi100.csv")
    for code, name in dict.items():
        print(code, name)
        save_table(kiwoom, name, code, date)
        insert_colmns(kiwoom, name, code)

    a = get_cached_data("068270")
    print(a)