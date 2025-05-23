import time
from pykiwoom.kiwoom import *
from datetime import datetime

def accountInfo():
    account_num = kiwoom.GetLoginInfo("ACCOUNT_CNT")  # 전체 계좌수
    accounts = kiwoom.GetLoginInfo("ACCNO")  # 전체 계좌 리스트
    user_id = kiwoom.GetLoginInfo("USER_ID")  # 사용자 ID
    user_name = kiwoom.GetLoginInfo("USER_NAME")  # 사용자명
    keyboard = kiwoom.GetLoginInfo("KEY_BSECGB")  # 키보드보안 해지여부
    firewall = kiwoom.GetLoginInfo("FIREW_SECGB")  # 방화벽 설정 여부

    print(accounts)

def getCode(kiwoom, n=0):# kospi  : 0, kosdaq : 10, etf: 8
    codes = kiwoom.GetCodeListByMarket(n)
    # print(len(codes), codes)

    return codes

def GetPrice(code):
    df = kiwoom.block_request("opt10004",
                              종목코드=code,
                              output="주식호가요청",
                              next=0)

    wanted_keys = ['매도최우선호가', '매도최우선잔량', '매수최우선호가', '매수최우선잔량']
    for key in wanted_keys:
        print(f"{key}: {df[key][0]}")

def basicInfo(code):
    df = kiwoom.block_request("opt10001",
                              종목코드=code,
                              output="주식기본정보",
                              next=0)

    # wanted_keys = ['시가총액', 'PER', '영업이익', '시가']
    wanted_keys = ['기준가', '시가', '고가', '저가', '현재가']  # 기준가 == 전일종가
    for key in wanted_keys:
        print(f"{key}: {df[key][0]}")

    return df

def sell(accountNumber, code, quantity):
    # 현재가 매수
    kiwoom.SendOrder("시장가매수", "0101", accountNumber, 1, code, quantity, 0, "03", "")

    # 현재가 매도
    kiwoom.SendOrder("시장가매도", "0101", accountNumber, 2, code, quantity, 0, "03", "")

def request_ohlcv(kiwoom, code, date):
    dfs = []
    df = kiwoom.block_request("opt10081", # 10081: 일봉, # 10082: 주봉, # 10083: 연봉
                              종목코드=code,
                              기준일자=date,
                              수정주가구분=1,
                              output="주식일봉차트조회",
                              next=0)
    dfs.append(df)

    while kiwoom.tr_remained:
        df = kiwoom.block_request("opt10081",
                                  종목코드=code,
                                  기준일자=date,
                                  수정주가구분=1,
                                  output="주식일봉차트조회",
                                  next=2)
        dfs.append(df)
        time.sleep(1)

    if df.empty:
        print("데이터 수신 실패")
        return

    data = pd.concat(dfs, ignore_index=True)
    print(f"수신된 전체 일봉 데이터 수: {len(data)}")

    df_filtered = data[['종목코드','시가', '현재가', '고가', '저가', '거래량', '일자']].copy()
    # 컬럼명 변경
    df_filtered.rename(columns={
        '종목코드': 'code',
        '시가': 'open',
        '현재가': 'close',
        '고가': 'high',
        '저가': 'low',
        '거래량': 'volume',
        '일자': 'timestamp'
    }, inplace=True)

    # 날짜 포맷으로 변환
    df_filtered['timestamp'] = pd.to_datetime(df_filtered['timestamp'], format='%Y%m%d')

    # 'open', 'close', 'high', 'low', 'volume' 컬럼을 숫자로 변환
    numeric_columns = ['open', 'close', 'high', 'low', 'volume']
    df_filtered[numeric_columns] = df_filtered[numeric_columns].apply(pd.to_numeric, errors='coerce')

    # 등락률 계산
    df_filtered['chg_rate'] = round(((df_filtered['close'] - df_filtered['open']) / df_filtered['open']) * 100, 2)

    return df_filtered


if __name__ == '__main__':
    kiwoom = Kiwoom()
    kiwoom.CommConnect(block=True)  # 블록 로그인: 로그인이 완료될 때까지 다음 줄의 코드가 수행되지 않고 블록킹
    codes = getCode(kiwoom, 10)

    i = 0
    while (True):
        if ( i > 11) : break

        df = basicInfo("005930")
        print(type(df))
        print(df['종목명'])

        time.sleep(1)
        i +=1

