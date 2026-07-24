import streamlit as st
import pandas as pd
import altair as alt
from pathlib import Path

# =====================================================
# 페이지 설정
# =====================================================
st.set_page_config(
    page_title="서울시 상권 분석 대시보드",
    page_icon="📊",
    layout="wide"
)

st.title("📊 서울시 상권 분석 대시보드")
st.markdown("---")

# =====================================================
# 데이터 읽기
# =====================================================
DATA_FILE = Path(__file__).parent / "서울시 상권분석서비스(추정매출-상권)_2024년-1.csv"

df = pd.read_csv(DATA_FILE, encoding="cp949")

# =====================================================
# 분기 컬럼 생성
# =====================================================
df["분기"] = (
    df["기준_년분기_코드"].astype(str).str[:4]
    + "년 "
    + df["기준_년분기_코드"].astype(str).str[-1]
    + "분기"
)

# =====================================================
# 사이드바
# =====================================================
st.sidebar.header("📂 데이터 필터")

# -----------------------------
# 분기
# -----------------------------
quarters = sorted(df["분기"].unique())

selected_quarters = st.sidebar.multiselect(
    "📅 분기 선택",
    options=["전체"] + quarters,
    default=["전체"]
)

# -----------------------------
# 상권유형
# -----------------------------
market_types = sorted(df["상권_구분_코드_명"].dropna().unique())

default_market = [
    x for x in ["골목상권", "전통시장"]
    if x in market_types
]

selected_market = st.sidebar.multiselect(
    "🏘️ 상권유형",
    options=market_types,
    default=default_market
)

# -----------------------------
# 업종
# -----------------------------
top5_service = (
    df.groupby("서비스_업종_코드_명")["당월_매출_금액"]
    .sum()
    .sort_values(ascending=False)
    .head(5)
    .index
    .tolist()
)

service_list = sorted(df["서비스_업종_코드_명"].dropna().unique())

selected_service = st.sidebar.multiselect(
    "🏷️ 업종",
    options=service_list,
    default=top5_service
)

# =====================================================
# 데이터 필터
# =====================================================
data = df.copy()

if "전체" not in selected_quarters:
    data = data[data["분기"].isin(selected_quarters)]

if selected_market:
    data = data[data["상권_구분_코드_명"].isin(selected_market)]

if selected_service:
    data = data[data["서비스_업종_코드_명"].isin(selected_service)]

# =====================================================
# KPI 계산
# =====================================================
sales = data["당월_매출_금액"].sum()
count = data["당월_매출_건수"].sum()

market_cnt = data["상권_코드_명"].nunique()
service_cnt = data["서비스_업종_코드_명"].nunique()

sales_eok = sales / 100000000
count_man = count / 10000

# =====================================================
# KPI
# =====================================================
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

quarter_text = (
    "전체"
    if "전체" in selected_quarters
    else ", ".join(selected_quarters)
)

st.info(
    f"""
📌 **현재 필터**

- 분기 : **{quarter_text}**
- 상권유형 : **{', '.join(selected_market)}**
- 업종 : **{len(selected_service):,}개 선택**
"""
)

# =====================================================
# 업종별 매출 TOP10
# =====================================================

top10 = (
    data.groupby(
        "서비스_업종_코드_명",
        as_index=False
    )["당월_매출_금액"]
    .sum()
)

top10.columns = ["업종", "매출액"]

top10["매출(억원)"] = top10["매출액"] / 100000000

top10 = (
    top10
    .sort_values(
        "매출액",
        ascending=False
    )
    .head(10)
)

st.subheader("🏆 분기 매출 TOP10 업종")

bars = (
    alt.Chart(top10)
    .mark_bar(
        cornerRadiusTopRight=6,
        cornerRadiusBottomRight=6
    )
    .encode(
        y=alt.Y(
            "업종:N",
            sort="-x",
            title=None
        ),
        x=alt.X(
            "매출(억원):Q",
            title="매출액 (억원)"
        ),
        tooltip=[
            alt.Tooltip(
                "업종:N"
            ),
            alt.Tooltip(
                "매출(억원):Q",
                title="매출액(억원)",
                format=",.1f"
            )
        ]
    )
)

text = (
    alt.Chart(top10)
    .mark_text(
        align="left",
        baseline="middle",
        dx=5,
        fontSize=13
    )
    .encode(
        y=alt.Y(
            "업종:N",
            sort="-x"
        ),
        x="매출(억원):Q",
        text=alt.Text(
            "매출(억원):Q",
            format=",.1f"
        )
    )
)

chart = (
    (bars + text)
    .properties(
        height=450
    )
)

st.altair_chart(
    chart,
    use_container_width=True
)
