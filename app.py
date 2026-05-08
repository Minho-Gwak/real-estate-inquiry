"""Streamlit 웹 앱 — 두 가지 조회를 한 페이지에서.

탭 1: 🏢 건축물 면적 조회   (main.py)
탭 2: 💰 개별공시지가 조회   (landprice.py)

실행: streamlit run app.py
배포 시 .streamlit/secrets.toml 또는 환경변수에:
    JUSO_API_KEY, DATA_GO_KR_KEY, VWORLD_API_KEY
"""

import io
import os
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

import streamlit as st

# Streamlit secrets → 환경변수 (모듈들이 환경변수에서 읽음).
try:
    for k in ("JUSO_API_KEY", "DATA_GO_KR_KEY", "VWORLD_API_KEY"):
        if k in st.secrets:
            os.environ[k] = st.secrets[k]
except Exception:
    pass

import main  # noqa: E402
import landprice  # noqa: E402


st.set_page_config(
    page_title="부동산 정보 조회",
    page_icon="🏢",
    layout="centered",
    initial_sidebar_state="collapsed",
)


# -------------------- 공통 CSS --------------------

CUSTOM_CSS = """
<style>
@import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.min.css');

:root {
    --ok-orange: #FF571F;
    --ok-orange-dark: #E54710;
    --ok-orange-light: #FFE5D9;
    --ok-text: #1A1A1A;
    --ok-text-soft: #555555;
    --ok-text-mute: #8B8B8B;
    --ok-bg: #F8F8F9;
    --ok-card: #FFFFFF;
    --ok-border: #ECECEE;
    --ok-border-strong: #D4D4D8;
}

html, body, [class*="css"], .stMarkdown, .stTextArea textarea,
.stButton button, .stDownloadButton button, .stTabs [data-baseweb="tab"] {
    font-family: 'Pretendard', -apple-system, BlinkMacSystemFont,
                 'Segoe UI', Roboto, 'Helvetica Neue', sans-serif !important;
    -webkit-font-smoothing: antialiased;
}

.block-container {
    padding-top: 4.5rem;
    padding-bottom: 4rem;
    max-width: 960px;
}

[data-testid="stSidebarCollapsedControl"] { display: none; }
/* Streamlit 기본 상단 툴바(Deploy 버튼 영역)가 콘텐츠를 가리지 않도록 투명/낮게. */
[data-testid="stHeader"] {
    background: transparent !important;
    height: 0 !important;
}
[data-testid="stToolbar"] { right: 8px; }

/* ===== 헤더 ===== */
.app-hero { margin: -8px 0 24px 0; }
.app-hero .badge {
    display: inline-block;
    background: var(--ok-orange-light);
    color: var(--ok-orange);
    padding: 5px 12px;
    border-radius: 999px;
    font-size: 12px;
    font-weight: 700;
    letter-spacing: 0.02em;
    margin-bottom: 14px;
}
.app-hero h1 {
    font-size: 36px;
    font-weight: 800;
    letter-spacing: -0.03em;
    color: var(--ok-text);
    margin: 0 0 10px 0;
    padding: 0;
    line-height: 1.2;
}
.app-hero p {
    color: var(--ok-text-soft);
    font-size: 15px;
    line-height: 1.65;
    margin: 0;
}

/* ===== 탭 (큰 pill 카드형) ===== */
.stTabs [data-baseweb="tab-list"] {
    gap: 12px;
    border-bottom: none;
    margin-bottom: 24px;
    background: var(--ok-card);
    padding: 8px;
    border-radius: 999px;
    border: 1px solid var(--ok-border);
}
.stTabs [data-baseweb="tab"] {
    height: 56px;
    flex: 1;
    padding: 0 24px;
    font-weight: 700;
    font-size: 18px;
    color: var(--ok-text-mute);
    background: transparent;
    border-radius: 999px !important;
    border: none;
    transition: all 0.2s;
    white-space: nowrap;
    display: flex;
    align-items: center;
    justify-content: center;
}
.stTabs [data-baseweb="tab"] p {
    font-size: 18px !important;
    font-weight: 700 !important;
}
.stTabs [data-baseweb="tab"]:hover {
    color: var(--ok-text);
    background: rgba(255, 87, 31, 0.06);
}
.stTabs [aria-selected="true"] {
    color: white !important;
    background: var(--ok-orange) !important;
    font-weight: 800 !important;
    border-bottom: none !important;
    box-shadow: 0 4px 14px rgba(255, 87, 31, 0.32);
}
.stTabs [aria-selected="true"] p {
    font-weight: 800 !important;
}
.stTabs [data-baseweb="tab-highlight"] { display: none !important; }
.stTabs [data-baseweb="tab-border"] { display: none !important; }

/* ===== 카드 ===== */
[data-testid="stVerticalBlockBorderWrapper"] {
    background: var(--ok-card);
    border: 1px solid var(--ok-border) !important;
    border-radius: 24px !important;
    padding: 26px 28px !important;
    box-shadow: 0 1px 2px rgba(0,0,0,0.02);
}

/* ===== 라벨 ===== */
label, .stTextArea label, .stTextInput label {
    font-weight: 700 !important;
    color: var(--ok-text) !important;
    font-size: 14px !important;
    margin-bottom: 8px !important;
}

/* ===== Textarea ===== */
.stTextArea textarea {
    border-radius: 16px !important;
    border: 1px solid var(--ok-border) !important;
    font-size: 14px !important;
    line-height: 1.65 !important;
    padding: 14px 16px !important;
    background: #FAFAFB !important;
    transition: border-color 0.15s, box-shadow 0.15s, background 0.15s;
    color: var(--ok-text) !important;
}
.stTextArea textarea:focus {
    border-color: var(--ok-orange) !important;
    box-shadow: 0 0 0 3px rgba(255,87,31,0.12) !important;
    background: var(--ok-card) !important;
}

/* ===== Primary 버튼 (조회 시작) — 오렌지 pill ===== */
.stButton > button[kind="primary"] {
    background: var(--ok-orange) !important;
    color: white !important;
    border: none !important;
    font-weight: 700 !important;
    font-size: 15px !important;
    border-radius: 999px !important;
    height: 50px;
    padding: 0 32px;
    box-shadow: 0 4px 14px rgba(255, 87, 31, 0.28) !important;
    transition: transform 0.15s, box-shadow 0.15s, background 0.15s;
}
.stButton > button[kind="primary"]:hover:not(:disabled) {
    background: var(--ok-orange-dark) !important;
    transform: translateY(-1px);
    box-shadow: 0 6px 20px rgba(255, 87, 31, 0.38) !important;
}
.stButton > button[kind="primary"]:active {
    transform: translateY(0);
}

/* ===== Download 버튼 — 다크 pill (오렌지와 위계 분리) ===== */
.stDownloadButton > button {
    background: var(--ok-text) !important;
    color: white !important;
    border: none !important;
    font-weight: 700 !important;
    font-size: 15px !important;
    border-radius: 999px !important;
    height: 50px;
    box-shadow: 0 4px 14px rgba(0, 0, 0, 0.12) !important;
    transition: transform 0.15s, box-shadow 0.15s, background 0.15s;
}
.stDownloadButton > button:hover {
    background: #000 !important;
    transform: translateY(-1px);
    box-shadow: 0 6px 20px rgba(0, 0, 0, 0.18) !important;
}

/* ===== 일반 버튼 (외곽선) ===== */
.stButton > button:not([kind="primary"]) {
    border-radius: 999px !important;
    border: 1px solid var(--ok-border-strong) !important;
    font-weight: 600 !important;
    color: var(--ok-text) !important;
    background: var(--ok-card) !important;
}

/* ===== Progress bar — 솔리드 오렌지 ===== */
.stProgress > div > div > div > div {
    background: var(--ok-orange) !important;
    border-radius: 999px !important;
}
.stProgress > div > div > div {
    background: var(--ok-orange-light) !important;
    border-radius: 999px !important;
    height: 8px !important;
}

/* ===== Alert ===== */
.stAlert { border-radius: 16px !important; border: none !important; }

/* ===== Expander ===== */
[data-testid="stExpander"] details {
    border-radius: 14px !important;
    border: 1px solid var(--ok-border) !important;
}
.streamlit-expanderHeader, [data-testid="stExpander"] summary {
    font-weight: 600 !important;
    color: var(--ok-text-soft) !important;
    border-radius: 14px !important;
    padding: 12px 16px !important;
}

/* ===== DataFrame ===== */
[data-testid="stDataFrame"] {
    border-radius: 16px;
    overflow: hidden;
    border: 1px solid var(--ok-border);
}

/* ===== 섹션 제목 ===== */
.section-title {
    font-size: 12px;
    font-weight: 700;
    color: var(--ok-orange);
    letter-spacing: 0.08em;
    text-transform: uppercase;
    margin: 0 0 16px 0;
}

/* ===== 요약 카드 ===== */
.summary-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 12px;
    margin-bottom: 18px;
}
.summary-item {
    background: var(--ok-bg);
    border: 1px solid var(--ok-border);
    border-radius: 18px;
    padding: 16px 18px;
}
.summary-item .label {
    font-size: 12px;
    color: var(--ok-text-mute);
    margin-bottom: 6px;
    font-weight: 600;
}
.summary-item .value {
    font-size: 26px;
    font-weight: 800;
    color: var(--ok-text);
    letter-spacing: -0.02em;
    line-height: 1;
}

/* ===== 푸터 ===== */
.app-footer {
    text-align: center;
    color: var(--ok-text-mute);
    font-size: 12px;
    margin-top: 32px;
}
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# -------------------- 헤더 --------------------

st.markdown(
    """
    <div class="app-hero">
        <span class="badge">REAL ESTATE INQUIRY</span>
        <h1>부동산정보 일괄 조회</h1>
        <p>지번 주소를 입력하면 <b>건축물 면적</b> 또는 <b>개별공시지가</b>를 자동으로 정리해 엑셀로 내려받습니다.</p>
    </div>
    """,
    unsafe_allow_html=True,
)


# -------------------- 공통 유틸 --------------------

def parse_addresses(raw: str) -> list[str]:
    return [a.strip() for a in raw.splitlines() if a.strip()]


def address_input_card(key_prefix: str, placeholder: str, help_text: str) -> tuple[str, bool]:
    """입력 카드 — 텍스트영역 + 시작 버튼. (raw_text, started)."""
    with st.container(border=True):
        st.markdown('<div class="section-title">조회 주소 입력</div>',
                    unsafe_allow_html=True)
        raw = st.text_area(
            "한 줄에 하나씩 지번 주소를 입력하세요",
            height=160,
            placeholder=placeholder,
            help=help_text,
            label_visibility="collapsed",
            key=f"{key_prefix}_addr_input",
        )
        col_btn, col_count = st.columns([2, 5])
        with col_btn:
            started = st.button("조회 시작", type="primary",
                                use_container_width=True, key=f"{key_prefix}_start")
        with col_count:
            n = len(parse_addresses(raw))
            if n:
                st.markdown(
                    f"<div style='padding-top:10px;color:#64748B;font-size:14px;'>"
                    f"입력된 주소 <b>{n}건</b></div>",
                    unsafe_allow_html=True,
                )
    return raw, started


def render_summary(n_addr: int, n_rows: int, n_errors: int, label_rows: str = "생성된 행"):
    err_color = "#DC2626" if n_errors else "#10B981"
    st.markdown(
        f"""
        <div class="summary-grid">
            <div class="summary-item">
                <div class="label">조회 주소</div>
                <div class="value">{n_addr:,}<span style="font-size:14px;color:#64748B;font-weight:500;"> 건</span></div>
            </div>
            <div class="summary-item">
                <div class="label">{label_rows}</div>
                <div class="value">{n_rows:,}<span style="font-size:14px;color:#64748B;font-weight:500;"> 건</span></div>
            </div>
            <div class="summary-item">
                <div class="label">에러/누락</div>
                <div class="value" style="color:{err_color}">{n_errors:,}<span style="font-size:14px;color:#64748B;font-weight:500;"> 건</span></div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# 미리보기 dataframe 컬럼별 천단위·소수점 포맷 ----------------------

BLD_COLUMN_CONFIG = {
    "지상층수": st.column_config.NumberColumn(format="%d"),
    "지하층수": st.column_config.NumberColumn(format="%d"),
    "대지면적(㎡)": st.column_config.NumberColumn(format="%,.2f"),
    "건축면적(㎡)": st.column_config.NumberColumn(format="%,.2f"),
    "연면적(㎡)": st.column_config.NumberColumn(format="%,.2f"),
    "용적률산정용연면적(㎡)": st.column_config.NumberColumn(format="%,.2f"),
    "전용면적(㎡)": st.column_config.NumberColumn(format="%,.2f"),
    "공용면적(㎡)": st.column_config.NumberColumn(format="%,.2f"),
    "사용승인일": st.column_config.DateColumn(format="YYYY-MM-DD"),
}


def _lp_column_config(years: list[int]) -> dict:
    cfg = {
        "면적(㎡)": st.column_config.NumberColumn(format="%,.2f"),
    }
    for y in years:
        cfg[f"{y}년 (원/㎡)"] = st.column_config.NumberColumn(format="%,d")
    return cfg


# -------------------- 탭 1: 건축물 면적 조회 --------------------

def render_building_tab():
    raw, started = address_input_card(
        "bld",
        placeholder=(
            "서울 강남구 역삼동 736-1\n"
            "경기도 평택시 고덕동 2711-2\n"
            "대구광역시 수성구 지산동 1275-4"
        ),
        help_text="도로명주소 대신 지번 주소를 사용하세요. 광역시·특별시는 띄어 써도 붙여 써도 됩니다.",
    )

    # 1) 새로 조회 시작한 경우만 실제 처리 + session_state에 저장.
    if started:
        addresses = parse_addresses(raw)
        if not addresses:
            st.warning("주소를 한 개 이상 입력해 주세요.")
        else:
            st.write("")
            with st.container(border=True):
                st.markdown('<div class="section-title">진행 상황</div>',
                            unsafe_allow_html=True)
                overall = st.progress(0.0, text=f"0 / {len(addresses)} 처리 중…")
                sub_slot = st.empty()
                log = st.expander("처리 로그 자세히 보기", expanded=False)

                all_rows: list[list] = []
                for i, query in enumerate(addresses, start=1):
                    with log:
                        st.markdown(f"**[{i}/{len(addresses)}]** `{query}`")
                    sub_bar = sub_slot.progress(
                        0.0,
                        text=f"[{i}/{len(addresses)}] {query} — 조회 중…",
                    )

                    def on_progress(done: int, total: int, _i=i, _q=query):
                        if total > 0:
                            sub_bar.progress(
                                min(done / total, 1.0),
                                text=f"[{_i}/{len(addresses)}] {_q} — 호별 면적 {done:,} / {total:,}",
                            )

                    rows = main.process_address(i, query, verbose=False, on_progress=on_progress)
                    all_rows.extend(rows)
                    with log:
                        note = ""
                        if rows and rows[0][-1]:
                            note = f" · _{rows[0][-1]}_"
                        st.markdown(f"&nbsp;&nbsp;→ **{len(rows)}행** 생성{note}",
                                    unsafe_allow_html=True)
                    overall.progress(i / len(addresses),
                                     text=f"{i} / {len(addresses)} 처리 완료")
                sub_slot.empty()

            st.session_state["bld_result"] = {
                "rows": all_rows,
                "n_addr": len(addresses),
                "ts": datetime.now(),
            }

    # 2) session_state에 결과가 있으면 항상 렌더 (탭 전환 후에도 유지).
    if "bld_result" in st.session_state:
        _render_building_result()


def _render_building_result():
    r = st.session_state["bld_result"]
    rows, n_addr, ts = r["rows"], r["n_addr"], r["ts"]

    n_rows = len(rows)
    n_errors = sum(
        1 for row in rows
        if row[-1] and any(k in str(row[-1]) for k in ("검색", "실패", "없음"))
    )

    # 다운로드용 엑셀은 매 렌더마다 재생성 (메모리 절약, 비용 미미)
    buf = io.BytesIO()
    main.write_output(rows, buf)
    buf.seek(0)

    st.write("")
    with st.container(border=True):
        st.markdown('<div class="section-title">조회 결과</div>',
                    unsafe_allow_html=True)
        render_summary(n_addr, n_rows, n_errors, label_rows="생성된 행")
        filename = f"건축물면적_{ts.strftime('%Y%m%d_%H%M%S')}.xlsx"
        st.download_button(
            "📥  엑셀 다운로드",
            data=buf,
            file_name=filename,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
            key="bld_download",
        )

    st.write("")
    with st.container(border=True):
        st.markdown('<div class="section-title">미리보기</div>',
                    unsafe_allow_html=True)
        columns = [c[2] for c in main.COL_SPEC]
        preview = [dict(zip(columns, row)) for row in rows]
        st.dataframe(
            preview,
            use_container_width=True,
            hide_index=True,
            height=380,
            column_config=BLD_COLUMN_CONFIG,
        )


# -------------------- 탭 2: 개별공시지가 조회 --------------------

def render_landprice_tab():
    raw, started = address_input_card(
        "lp",
        placeholder=(
            "서울 강남구 역삼동 736-1\n"
            "경기도 평택시 고덕동 2711-2\n"
            "대구광역시 수성구 지산동 1275-4"
        ),
        help_text="최근 3개년의 개별공시지가(원/㎡)를 조회합니다. 5/31 이전엔 작년부터 3개년.",
    )

    if started:
        addresses = parse_addresses(raw)
        if not addresses:
            st.warning("주소를 한 개 이상 입력해 주세요.")
        else:
            years = landprice.determine_target_years()

            st.write("")
            with st.container(border=True):
                st.markdown('<div class="section-title">진행 상황</div>',
                            unsafe_allow_html=True)
                overall = st.progress(0.0, text=f"0 / {len(addresses)} 처리 중…")
                log = st.expander("처리 로그 자세히 보기", expanded=False)

                results: list[landprice.LandPriceResult | None] = [None] * len(addresses)
                completed = 0
                with ThreadPoolExecutor(max_workers=4) as ex:
                    futures = {
                        ex.submit(landprice.lookup_landprice, q, years): idx
                        for idx, q in enumerate(addresses)
                    }
                    for fut in as_completed(futures):
                        idx = futures[fut]
                        try:
                            results[idx] = fut.result()
                        except Exception as e:
                            results[idx] = landprice.LandPriceResult(
                                query=addresses[idx], matched_jibun=None, pnu=None,
                                years=years, prices={y: None for y in years},
                                area=None, land_use=None, zone=None,
                                status="api_error", error_msg=str(e),
                            )
                        completed += 1
                        r = results[idx]
                        with log:
                            bullet = {"ok": "✅", "not_found": "❓", "no_data": "—",
                                      "api_error": "⚠️"}.get(r.status, "•")
                            st.markdown(
                                f"{bullet} **[{idx + 1}]** `{r.query}` → {r.status}"
                                + (f" · _{r.error_msg}_" if r.error_msg else "")
                            )
                        overall.progress(
                            completed / len(addresses),
                            text=f"{completed} / {len(addresses)} 처리 완료",
                        )

            final_results = [r for r in results if r is not None]
            st.session_state["lp_result"] = {
                "results": final_results,
                "years": years,
                "n_addr": len(addresses),
                "ts": datetime.now(),
            }

    if "lp_result" in st.session_state:
        _render_landprice_result()


def _render_landprice_result():
    state = st.session_state["lp_result"]
    final_results: list[landprice.LandPriceResult] = state["results"]
    years: list[int] = state["years"]
    n_addr: int = state["n_addr"]
    ts: datetime = state["ts"]

    buf = io.BytesIO()
    landprice.write_landprice_xlsx(final_results, buf)
    buf.seek(0)

    n_ok = sum(1 for r in final_results if r.status == "ok")
    n_errors = n_addr - n_ok

    st.write("")
    with st.container(border=True):
        st.markdown('<div class="section-title">조회 결과</div>',
                    unsafe_allow_html=True)
        render_summary(n_addr, n_ok, n_errors, label_rows="조회 성공")
        st.markdown(
            f"<div style='color:#64748B;font-size:13px;margin-bottom:10px;'>"
            f"조회 연도: <b>{years[0]} · {years[1]} · {years[2]}</b> (단위: 원/㎡)</div>",
            unsafe_allow_html=True,
        )
        filename = f"개별공시지가_{ts.strftime('%Y%m%d_%H%M%S')}.xlsx"
        st.download_button(
            "📥  엑셀 다운로드",
            data=buf,
            file_name=filename,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
            key="lp_download",
        )

    st.write("")
    with st.container(border=True):
        st.markdown('<div class="section-title">미리보기</div>',
                    unsafe_allow_html=True)
        preview = []
        for i, r in enumerate(final_results, 1):
            row = {
                "번호": i,
                "입력주소": r.query,
                "매칭지번": r.matched_jibun or "",
                "PNU": r.pnu or "",
                "지목": r.land_use or "",
                "용도지역": r.zone or "",
                "면적(㎡)": r.area,
            }
            for y in years:
                row[f"{y}년 (원/㎡)"] = r.prices[y]
            note = ""
            if r.status == "not_found":
                note = r.error_msg or "주소 검색 실패"
            elif r.status == "api_error":
                note = r.error_msg or "API 오류"
            elif r.status == "no_data":
                note = "데이터 없음"
            elif r.error_msg:
                note = r.error_msg
            row["비고"] = note
            preview.append(row)
        st.dataframe(
            preview,
            use_container_width=True,
            hide_index=True,
            height=380,
            column_config=_lp_column_config(years),
        )


# -------------------- 탭 렌더 --------------------

tab_bld, tab_lp = st.tabs(["건축물 정보 조회", "개별공시지가 조회"])
with tab_bld:
    render_building_tab()
with tab_lp:
    render_landprice_tab()


# -------------------- 푸터 --------------------

st.markdown(
    '<div class="app-footer">데이터 출처 · 국토교통부 건축물대장정보 / 행정안전부 도로명주소 / VWorld 개별공시지가</div>',
    unsafe_allow_html=True,
)
