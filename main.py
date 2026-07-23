"""
서울시 상권분석 Streamlit 대시보드

- main.py와 같은 폴더에 있는 CP949 CSV 파일을 읽습니다.
- pandas, chardet 같은 추가 라이브러리를 사용하지 않습니다.
- Python 표준 라이브러리와 Streamlit만 사용합니다.
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Dict, List, Tuple

import streamlit as st


# -----------------------------------------------------------------------------
# 1. 기본 설정
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="서울시 상권분석 대시보드",
    page_icon="🏙️",
    layout="wide",
)

# main.py와 같은 폴더에 둘 CSV 파일명입니다.
# 실제 파일명이 다르면 아래 문자열만 수정하면 됩니다.
DATA_FILE_NAME = "서울시_상권분석_열이름변경_CP949.csv"

# 집계에 필요한 열 이름입니다.
REQUIRED_COLUMNS = {
    "기준_년분기_코드",
    "상권이름",
    "업종",
    "분기매출액",
    "분기거래건수",
}


# -----------------------------------------------------------------------------
# 2. 화면 스타일
# -----------------------------------------------------------------------------
st.markdown(
    """
    <style>
        /* 화면 위쪽의 기본 여백을 조금 줄입니다. */
        .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
        }

        /* KPI 카드의 테두리와 배경을 보기 좋게 정리합니다. */
        div[data-testid="stMetric"] {
            background: linear-gradient(135deg, #ffffff 0%, #f7f9fc 100%);
            border: 1px solid #e2e8f0;
            border-radius: 16px;
            padding: 20px 18px;
            min-height: 142px;
            box-shadow: 0 4px 14px rgba(15, 23, 42, 0.06);
        }

        div[data-testid="stMetricLabel"] {
            font-weight: 700;
        }

        div[data-testid="stMetricValue"] {
            font-weight: 800;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


# -----------------------------------------------------------------------------
# 3. 데이터 관련 함수
# -----------------------------------------------------------------------------
def find_data_file() -> Path:
    """main.py와 같은 폴더에서 사용할 CSV 파일을 찾습니다."""
    app_folder = Path(__file__).resolve().parent
    expected_file = app_folder / DATA_FILE_NAME

    # 지정한 파일이 있으면 그 파일을 가장 먼저 사용합니다.
    if expected_file.exists():
        return expected_file

    # 파일명이 달라진 경우를 대비해 같은 폴더의 CSV도 확인합니다.
    csv_files = sorted(app_folder.glob("*.csv"))

    if len(csv_files) == 1:
        return csv_files[0]

    if not csv_files:
        raise FileNotFoundError(
            f"'{DATA_FILE_NAME}' 파일을 main.py와 같은 폴더에서 찾을 수 없습니다."
        )

    raise FileNotFoundError(
        "같은 폴더에 CSV 파일이 여러 개 있습니다. "
        f"DATA_FILE_NAME에 사용할 파일명을 지정해 주세요: {[p.name for p in csv_files]}"
    )


def open_csv_with_fallback(file_path: Path):
    """
    CSV 파일을 엽니다.

    현재 데이터는 CP949이므로 CP949를 먼저 사용합니다.
    파일이 UTF-8로 교체될 가능성도 고려해 UTF-8-SIG를 두 번째로 시도합니다.
    별도의 인코딩 감지 라이브러리는 사용하지 않습니다.
    """
    encodings = ("cp949", "utf-8-sig")
    last_error: UnicodeDecodeError | None = None

    for encoding in encodings:
        try:
            file = file_path.open("r", encoding=encoding, newline="")

            # 실제로 일부 내용을 읽어 디코딩 오류가 있는지 먼저 확인합니다.
            file.read(4096)
            file.seek(0)
            return file, encoding
        except UnicodeDecodeError as error:
            last_error = error
            try:
                file.close()
            except Exception:
                pass

    raise UnicodeError(
        "CSV 파일을 CP949 또는 UTF-8로 읽을 수 없습니다."
    ) from last_error


def to_number(value: str) -> float:
    """쉼표가 포함된 문자열을 숫자로 바꿉니다. 빈 값은 0으로 처리합니다."""
    text = (value or "").strip().replace(",", "")

    if not text:
        return 0.0

    try:
        return float(text)
    except ValueError:
        return 0.0


@st.cache_data(show_spinner=False)
def load_data(file_path: str, modified_time: float) -> Tuple[List[Dict], str]:
    """
    CSV에서 KPI 계산에 필요한 열만 읽습니다.

    modified_time은 함수 안에서 직접 사용하지 않지만, 파일이 변경되면
    Streamlit 캐시가 자동으로 갱신되도록 캐시 키에 포함합니다.
    """
    del modified_time

    path = Path(file_path)
    rows: List[Dict] = []

    file, encoding = open_csv_with_fallback(path)

    with file:
        reader = csv.DictReader(file)
        fieldnames = set(reader.fieldnames or [])
        missing_columns = REQUIRED_COLUMNS - fieldnames

        if missing_columns:
            missing_text = ", ".join(sorted(missing_columns))
            raise KeyError(f"필수 열을 찾을 수 없습니다: {missing_text}")

        for row in reader:
            rows.append(
                {
                    "quarter": (row.get("기준_년분기_코드") or "").strip(),
                    "revenue": to_number(row.get("분기매출액", "")),
                    "transactions": to_number(row.get("분기거래건수", "")),
                    "market": (row.get("상권이름") or "").strip(),
                    "industry": (row.get("업종") or "").strip(),
                }
            )

    return rows, encoding


def quarter_label(quarter_code: str) -> str:
    """20241 같은 분기 코드를 '2024년 1분기' 형식으로 표시합니다."""
    code = str(quarter_code).strip()

    if len(code) == 5 and code.isdigit():
        return f"{code[:4]}년 {code[4]}분기"

    return code


def quarter_sort_key(quarter_code: str):
    """분기 코드를 연도와 분기 순서대로 정렬하기 위한 기준입니다."""
    code = str(quarter_code).strip()

    if len(code) == 5 and code.isdigit():
        return int(code[:4]), int(code[4])

    return 0, code


def format_eok_won(value: float) -> str:
    """원 단위 금액을 억 원 단위로 바꾸고 천 단위 쉼표를 넣습니다."""
    return f"{value / 100_000_000:,.2f} 억원"


def format_man_cases(value: float) -> str:
    """거래건수를 만 건 단위로 바꾸고 천 단위 쉼표를 넣습니다."""
    return f"{value / 10_000:,.2f} 만 건"


# -----------------------------------------------------------------------------
# 4. 데이터 불러오기
# -----------------------------------------------------------------------------
st.title("🏙️ 서울시 상권분석 대시보드")
st.caption("📊 분기를 선택하면 아래의 핵심 지표가 자동으로 갱신됩니다.")

try:
    data_path = find_data_file()
    data, used_encoding = load_data(
        str(data_path),
        data_path.stat().st_mtime,
    )
except (FileNotFoundError, UnicodeError, KeyError, csv.Error) as error:
    st.error(f"🚨 데이터를 불러올 수 없습니다.\n\n{error}")
    st.stop()

if not data:
    st.warning("⚠️ CSV 파일에 분석할 데이터가 없습니다.")
    st.stop()


# -----------------------------------------------------------------------------
# 5. 분기 필터
# -----------------------------------------------------------------------------
quarter_codes = sorted(
    {row["quarter"] for row in data if row["quarter"]},
    key=quarter_sort_key,
)

# 화면에는 한글 분기명을 보여주되, 실제 집계에는 원본 코드를 사용합니다.
quarter_options = ["전체"] + quarter_codes

selected_quarter = st.selectbox(
    "🗓️ 분석할 분기를 선택하세요",
    options=quarter_options,
    index=0,  # 첫 화면의 기본 선택값은 '전체'입니다.
    format_func=lambda value: "전체 분기" if value == "전체" else quarter_label(value),
)

if selected_quarter == "전체":
    filtered_data = data
    selected_label = "전체 분기"
else:
    filtered_data = [
        row for row in data if row["quarter"] == selected_quarter
    ]
    selected_label = quarter_label(selected_quarter)


# -----------------------------------------------------------------------------
# 6. KPI 계산
# -----------------------------------------------------------------------------
total_revenue = sum(row["revenue"] for row in filtered_data)
total_transactions = sum(row["transactions"] for row in filtered_data)

# 빈 문자열은 상권·업종 개수에서 제외합니다.
market_count = len({row["market"] for row in filtered_data if row["market"]})
industry_count = len({row["industry"] for row in filtered_data if row["industry"]})

st.markdown(f"### 📌 {selected_label} 핵심 지표")

# 화면을 가로 4칸으로 나눕니다.
col1, col2, col3, col4 = st.columns(4, gap="medium")

with col1:
    st.metric(
        label="💰 총 분기 매출액",
        value=format_eok_won(total_revenue),
    )

with col2:
    st.metric(
        label="🧾 총 분기 거래건수",
        value=format_man_cases(total_transactions),
    )

with col3:
    st.metric(
        label="🏘️ 분석 상권 수",
        value=f"{market_count:,} 개",
    )

with col4:
    st.metric(
        label="🛍️ 업종 종류",
        value=f"{industry_count:,} 개",
    )

st.divider()
st.caption(
    f"📁 사용 파일: {data_path.name}  |  🔤 읽은 인코딩: {used_encoding.upper()}"
)
