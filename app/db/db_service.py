import pandas as pd
import time
import datetime
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, Float, String, DateTime
from sqlalchemy.orm import sessionmaker
from app.config import DB_URL
from app.api.kiwoomAPI import *

# DB 연결
engine = create_engine(DB_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

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

# OHLCV 데이터 요청 및 저장 함수
def save_table(kiwoom, table_name, code, date=""):
    ohlcv_table = createTable(table_name)
    df_filtered = request_ohlcv(kiwoom, code, date)

    # DataFrame을 dict 리스트로 변환
    ohlcv_data_list = df_filtered[['code', 'open', 'close', 'high', 'low', 'chg_rate', 'volume', 'timestamp']].to_dict('records')

    # 데이터베이스에 저장 (대량 삽입)
    if ohlcv_data_list:
        save_ohlcv_bulk(ohlcv_table, ohlcv_data_list)
        print(f"{code} 종목의 데이터 {len(ohlcv_data_list)}개가 {table_name} 테이블에 저장되었습니다.")
    else:
        print("저장할 데이터가 없습니다.")

    return df_filtered

def insert_colmns(kiwoom, table_name, code):
    ohlcv_table = createTable(table_name)
    df = kiwoom.block_request("opt10001",
                              종목코드=code,
                              output="주식기본정보",
                              next=0)

    ohlcv_data_list ={
        'code' : code,
        'open' : df['시가'][0],
        'close': df['현재가'][0],
        'high': df['고가'][0],
        'low': df['저가'][0],
        'chg_rate': df['등락율'][0],
        'volume': df['거래량'][0],
        'timestamp' : datetime.now()
    }

    if ohlcv_data_list:
        save_ohlcv(ohlcv_table, ohlcv_data_list)
        print(f"{code} 종목의 데이터 {len(ohlcv_data_list)}개가 {table_name} 테이블에 저장되었습니다.")
    else:
        print("저장할 데이터가 없습니다.")


if __name__ == "__main__":
    kiwoom = Kiwoom()
    kiwoom.CommConnect(block=True)
    code = '042660'
    table_name = kiwoom.GetMasterCodeName(code)
    date = ""  # 기준일자 (빈 문자열로 최신 데이터 요청)

    save_table(kiwoom, table_name, code)
    df = insert_colmns(kiwoom,table_name, code)