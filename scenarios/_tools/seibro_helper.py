# ── SEIBRO 공통 셀 (모든 시나리오 노트북 공통) ─────────────────────────────
# Colab: 왼쪽 🔑(Secrets)에 아래 SECRETS 이름으로 값을 넣고 "노트북 액세스"를 켜세요.
#        SEIBRO_API_KEY = 예탁결제원 SEIBRO Open API 인증키 (https://seibro.or.kr/OpenPlatform)
#        DART_API_KEY = OpenDART 인증키 (DART 데이터를 쓰는 노트북만)
#        KRX_ID / KRX_PW = KRX 정보데이터시스템 계정 (KRX 데이터를 쓰는 노트북만)
# 로컬: 환경변수 또는 작업 폴더(레포 루트)의 .env 를 읽습니다.
# 키·비밀번호 값은 어디에도 출력하지 않습니다. 있는지 여부만 보여 줍니다.
import os, sys, warnings
from datetime import date, datetime, timedelta

import pandas as pd

IN_COLAB = "google.colab" in sys.modules
warnings.filterwarnings("ignore", message="Unverified HTTPS request")

if IN_COLAB:
    from google.colab import userdata
    for _name in SECRETS:  # noqa: F821  (빌더가 이 셀 맨 위에 SECRETS 목록을 넣음)
        if os.environ.get(_name):
            continue
        try:
            _v = userdata.get(_name)
        except Exception:
            _v = None
        if not _v:
            from getpass import getpass
            _v = getpass(f"{_name}: ")
        os.environ[_name] = _v.strip()
else:
    from dotenv import find_dotenv, load_dotenv
    load_dotenv(find_dotenv(usecwd=True))

_missing = [
    n for n in SECRETS  # noqa: F821
    if not os.environ.get(n) and (IN_COLAB or not n.startswith("KRX_"))
]
if _missing:
    raise RuntimeError(f"{_missing} 가 없습니다. Colab Secrets 또는 .env 에 넣어 주세요.")

pd.set_option("display.max_columns", 30)
pd.set_option("display.width", 200)
pd.set_option("display.max_colwidth", 50)
pd.set_option("display.float_format", lambda v: f"{v:,.2f}")


def won(v, digits=1):
    """원 → '1.2조' / '5,027억' / '3,400만'."""
    if v is None or pd.isna(v):
        return "-"
    a = abs(v)
    if a >= 1e12:
        return f"{v / 1e12:.{digits}f}조"
    if a >= 1e8:
        return f"{v / 1e8:,.0f}억"
    if a >= 1e4:
        return f"{v / 1e4:,.0f}만"
    return f"{v:,.0f}"


def shares(v):
    """주식수 → '23,607,980주'."""
    return "-" if v is None or pd.isna(v) else f"{int(v):,}주"


# 한글 차트 폰트
import matplotlib.pyplot as plt
try:
    import koreanize_matplotlib  # noqa: F401  (Colab: 위 셀에서 설치)
except ImportError:
    if sys.platform.startswith("win"):
        plt.rcParams["font.family"] = "Malgun Gothic"
    elif sys.platform == "darwin":
        plt.rcParams["font.family"] = "AppleGothic"
plt.rcParams["axes.unicode_minus"] = False

def _status(n):
    if os.environ.get(n):
        return "있음"
    # 로컬에서 krx-data-api를 편집 설치(pip install -e)했다면 그 레포의 .env를 패키지가 직접 읽는다
    return "없음" if IN_COLAB or not n.startswith("KRX_") else "krx-data-api 자체 .env 사용"


print("SEIBRO 준비 완료", "(Colab)" if IN_COLAB else "(로컬)",
      "| " + ", ".join(f"{n}: {_status(n)}" for n in SECRETS))  # noqa: F821
