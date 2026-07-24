import streamlit as st
import pandas as pd
from pathlib import Path

# --------------------------------------------------
# 페이지 설정
# --------------------------------------------------
st.set_page_config(
    page_title="서울시 상권 분석 대시보드",
    page_icon="📊",
    layout="wide"
)

st.title("📊 서울시 상권 분석 대시보드")
st.markdown("---")

# --------------------------------------------------
# 데이터 읽기
# --------------------------------------------------
DATA_FILE = Path(__file__).parent / "서울시 상권분석서비스(추정매출-상권)_2024년-1.csv"

df = pd.read_csv(DATA_FILE, encoding="cp949")

# --------------------------------------------------
# 분기 컬럼 생성
# 예) 20241 → 2024년 1분기
# --------------------------------------------------
df["분기"] = (
    df["기준_년분기_코드"]
    .astype(str)
    .str[:4]
    + "년 "
    + df["기준_년분기_코드"].astype(str).str[-1]
    + "분기"
)

# --------------------------------------------------
# 사이드바
# --------------------------------------------------
st.sidebar.header("🔎 분석 조건")

quarters = sorted(df["분기"].unique())

selected = st.sidebar.selectbox(
    "📅 분기 선택",
    ["전체"] + quarters
)

if selected == "전체":
    data = df.copy()
else:
    data = df[df["분기"] == selected]

# --------------------------------------------------
# 메트릭 계산
# --------------------------------------------------
sales = data["당월_매출_금액"].sum()
count = data["당월_매출_건수"].sum()

market_cnt = data["상권_코드_명"].nunique()
service_cnt = data["서비스_업종_코드_명"].nunique()

sales_eok = sales / 100000000      # 억원
count_man = count / 10000          # 만건

# --------------------------------------------------
# 메트릭 표시
# --------------------------------------------------
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "💰 총 분기 매출액",
        f"{sales_eok:,.1f} 억원"
    )

with col2:
    st.metric(
        "🛒 총 분기 거래건수",
        f"{count_man:,.1f} 만건"
    )

with col3:
    st.metric(
        "🏙️ 분석 상권 수",
        f"{market_cnt:,}"
    )

with col4:
    st.metric(
        "🏷️ 업종 종류",
        f"{service_cnt:,}"
    )

st.markdown("---")

st.info(
    f"📌 현재 분석 대상 : **{selected}**"
)
