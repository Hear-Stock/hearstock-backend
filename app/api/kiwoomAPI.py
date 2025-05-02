from pykiwoom.kiwoom import *

def accountInfo():
    account_num = kiwoom.GetLoginInfo("ACCOUNT_CNT")  # 전체 계좌수
    accounts = kiwoom.GetLoginInfo("ACCNO")  # 전체 계좌 리스트
    user_id = kiwoom.GetLoginInfo("USER_ID")  # 사용자 ID
    user_name = kiwoom.GetLoginInfo("USER_NAME")  # 사용자명
    keyboard = kiwoom.GetLoginInfo("KEY_BSECGB")  # 키보드보안 해지여부
    firewall = kiwoom.GetLoginInfo("FIREW_SECGB")  # 방화벽 설정 여부

    print(accounts)

def getCode(n):
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

    wanted_keys = ['시가총액', 'PER', '영업이익', '시가']
    for key in wanted_keys:
        print(f"{key}: {df[key][0]}")

def sell(accountNumber, code, quantity):
    # 현재가 매수
    kiwoom.SendOrder("시장가매수", "0101", accountNumber, 1, code, quantity, 0, "03", "")

    # 현재가 매도
    kiwoom.SendOrder("시장가매도", "0101", accountNumber, 2, code, quantity, 0, "03", "")


if __name__ == '__main__':
    kiwoom = Kiwoom()
    kiwoom.CommConnect(block=True)  # 블록 로그인: 로그인이 완료될 때까지 다음 줄의 코드가 수행되지 않고 블록킹

    accountInfo()