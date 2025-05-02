## 키움 증권 API 환경 세팅하기

LINK: <[키움증권Open API](https://www.kiwoom.com/h/customer/download/VOpenApiInfoView)>
* API 신청, 모듈 다운로드

아나콘다 32비트 가상환경 생성
```
# CONDA_FORCE_32BIT 환경 변수를 1로 설정
set CONDA_FORCE_32BIT=1

# 32비트 가상환경 셍성. 
conda create -n (envName) python=3.8 anaconda

# 가상환경이 만들어 졌는지 확인
conda env list
```
python 환경 확인
```
import platform
print(platform.architecture())
> ('32bit', 'WindowsPE')
```
