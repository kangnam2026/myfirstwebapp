# ======================================================
# 사이드바 - 데이터 필터
# ======================================================

st.sidebar.header("📂 데이터 필터")

# -----------------------------
# 1. 분기
# -----------------------------
quarters = sorted(df["분기"].unique())

selected_quarters = st.sidebar.multiselect(
    "📅 분기 선택",
    options=["전체"] + quarters,
    default=["전체"]
)

# -----------------------------
# 2. 상권유형
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
# 3. 업종
# -----------------------------
# 전체 데이터 기준 매출 상위 5개 업종
top5_service = (
    df.groupby("서비스_업종_코드_명")["당월_매출_금액"]
      .sum()
      .sort_values(ascending=False)
      .head(5)
      .index
      .tolist()
)

services = sorted(df["서비스_업종_코드_명"].dropna().unique())

selected_service = st.sidebar.multiselect(
    "🏷️ 업종",
    options=services,
    default=top5_service
)

# ======================================================
# 필터 적용
# ======================================================

data = df.copy()

# 분기
if "전체" not in selected_quarters:
    data = data[data["분기"].isin(selected_quarters)]

# 상권유형
if selected_market:
    data = data[data["상권_구분_코드_명"].isin(selected_market)]

# 업종
if selected_service:
    data = data[data["서비스_업종_코드_명"].isin(selected_service)]
