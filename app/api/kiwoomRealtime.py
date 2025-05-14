import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QAxContainer import QAxWidget
from PyQt5.QtCore import QTimer

class RealTimeKiwoom:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.ocx = QAxWidget("KHOPENAPI.KHOpenAPICtrl.1")

        self.ocx.OnEventConnect.connect(self.login_slot)
        self.ocx.OnReceiveRealData.connect(self.realdata_slot)

        self.ocx.dynamicCall("CommConnect()")
        print("로그인 요청 중...")

    def login_slot(self, err_code):
        if err_code == 0:
            print("로그인 성공")

            # 실시간 등록: 현재가(10), 체결시간(20)
            self.ocx.dynamicCall(
                "SetRealReg(QString, QString, QString, QString)",
                "1000", "005930", "10", "0"
            )
            print("실시간 데이터 등록 완료")
        else:
            print(f"로그인 실패: 에러코드 {err_code}")
            self.app.quit()

    def realdata_slot(self, code, realtype, realdata):
        if realtype == "주식시세":
            price = self.ocx.dynamicCall("GetCommRealData(QString, int)", code, 10).strip()
            print(f"[{code}] 현재가: {price}")

    def run(self):
        self.app.exec_()

if __name__ == "__main__":
    kiwoom = RealTimeKiwoom()
    kiwoom.run()
