from sqlalchemy import create_engine, MetaData, Table, Column, Integer, Float, String, DateTime
from sqlalchemy.orm import sessionmaker
from app.config import DB_URL

# DB 연결
engine = create_engine(DB_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 테이블 정의
metadata = MetaData()

ohlcv_table = Table(
    'stock_ohlcv', metadata,
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

metadata.create_all(bind=engine)

# DB 저장 함수
def save_ohlcv(ohlcv_data: dict):
    with engine.connect() as conn:
        insert_stmt = ohlcv_table.insert().values(**ohlcv_data)
        conn.execute(insert_stmt)
