import pandas as pd


def getKospiCodes(filePath):
    kospi = pd.read_csv(filePath, dtype={'종목코드': str})
    # 콤마 제거 → 숫자형으로 변환
    kospi['상장시가총액(원)'] = kospi['상장시가총액(원)'].str.replace(',', '').astype(float)
    # 정렬
    kospi = kospi.sort_values(by="상장시가총액(원)", ascending=False)

    top100 = kospi.head(3)
    codes = dict(zip(top100['종목코드'], top100['종목명']))

    return codes


def getKosdaqCodes(filePath):
    kosdaq = pd.read_csv(filePath, dtype={'종목코드': str})
    # 콤마 제거 → 숫자형으로 변환
    kosdaq['상장시가총액(원)'] = kosdaq['상장시가총액(원)'].str.replace(',', '').astype(float)
    # 정렬
    kosdaq = kosdaq.sort_values(by="상장시가총액(원)", ascending=False)

    top100 = kosdaq.head(100)
    codes = dict(zip(top100['종목코드'], top100['종목명']))

    return codes