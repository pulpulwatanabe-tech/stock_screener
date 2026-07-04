import streamlit as st
import yfinance as yf
import pandas as pd
import ta
import math

st.set_page_config(page_title="株スクリーニングツール", page_icon="📈", layout="wide")
st.title("📈 株スクリーニングツール")
st.caption("RSIで割安株を自動抽出 ＋ ゴールデンクロス予兆検知")

# 日経225全銘柄
NIKKEI225 = """1332.T
1605.T
1721.T
1801.T
1802.T
1803.T
1808.T
1812.T
1925.T
1928.T
1963.T
2002.T
2269.T
2282.T
2413.T
2432.T
2501.T
2502.T
2503.T
2531.T
2768.T
2801.T
2802.T
2871.T
2914.T
3086.T
3092.T
3099.T
3289.T
3382.T
3401.T
3402.T
3405.T
3407.T
3436.T
3659.T
3861.T
3863.T
4004.T
4005.T
4021.T
4042.T
4043.T
4061.T
4063.T
4151.T
4183.T
4188.T
4202.T
4204.T
4208.T
4324.T
4452.T
4502.T
4503.T
4506.T
4507.T
4519.T
4523.T
4543.T
4568.T
4578.T
4661.T
4689.T
4704.T
4751.T
4755.T
4901.T
4902.T
4911.T
5001.T
5002.T
5019.T
5020.T
5101.T
5105.T
5108.T
5201.T
5202.T
5214.T
5232.T
5233.T
5301.T
5332.T
5333.T
5401.T
5406.T
5411.T
5413.T
5541.T
5631.T
5703.T
5706.T
5711.T
5713.T
5714.T
5715.T
5801.T
5802.T
5803.T
6022.T
6098.T
6103.T
6113.T
6146.T
6178.T
6273.T
6301.T
6302.T
6305.T
6326.T
6361.T
6367.T
6370.T
6371.T
6395.T
6412.T
6417.T
6471.T
6472.T
6473.T
6501.T
6503.T
6504.T
6506.T
6526.T
6586.T
6594.T
6645.T
6674.T
6701.T
6702.T
6703.T
6724.T
6752.T
6753.T
6754.T
6758.T
6762.T
6770.T
6806.T
6841.T
6857.T
6861.T
6902.T
6920.T
6952.T
6954.T
6963.T
6971.T
6976.T
6981.T
7003.T
7004.T
7011.T
7012.T
7013.T
7186.T
7201.T
7202.T
7203.T
7205.T
7211.T
7261.T
7267.T
7269.T
7270.T
7272.T
7731.T
7733.T
7735.T
7741.T
7751.T
7752.T
7762.T
7832.T
7911.T
7912.T
7951.T
7974.T
8001.T
8002.T
8003.T
8015.T
8031.T
8035.T
8053.T
8056.T
8058.T
8233.T
8252.T
8253.T
8267.T
8303.T
8304.T
8306.T
8308.T
8309.T
8316.T
8354.T
8355.T
8411.T
8601.T
8604.T
8630.T
8697.T
8725.T
8750.T
8766.T
8795.T
9001.T
9005.T
9007.T
9008.T
9009.T
9020.T
9021.T
9022.T
9064.T
9101.T
9104.T
9107.T
9147.T
9201.T
9202.T
9301.T
9432.T
9433.T
9434.T
9501.T
9502.T
9503.T
9531.T
9532.T
9602.T
9613.T
9735.T
9766.T
9983.T
9984.T"""

def safe_float(val):
    try:
        f = float(val)
        if math.isnan(f):
            return None
        return f
    except:
        return None

def detect_gc_sign(hist, short_window=25, long_window=75):
    if len(hist) < long_window + 5:
        return None, None, None
    hist = hist.copy()
    hist["SMA_short"] = hist["Close"].rolling(short_window).mean()
    hist["SMA_long"] = hist["Close"].rolling(long_window).mean()
    hist["gap_pct"] = (hist["SMA_short"] - hist["SMA_long"]) / hist["SMA_long"] * 100
    hist = hist.dropna(subset=["SMA_short", "SMA_long", "gap_pct"])
    if len(hist) < 5:
        return None, None, None
    current_gap = safe_float(hist["gap_pct"].iloc[-1])
    if current_gap is None:
        return None, None, None
    recent = hist["gap_pct"].tail(5)
    slope = safe_float(recent.iloc[-1] - recent.iloc[0])
    if slope is None:
        return None, None, None
    if current_gap < 0 and slope > 0:
        days_to_cross = abs(current_gap) / (slope / 5) if slope != 0 else None
        est = round(days_to_cross, 1) if days_to_cross and days_to_cross < 60 else None
        return round(current_gap, 2), round(slope, 3), est
    else:
        return None, None, None

st.sidebar.header("⚙️ スクリーニング条件")
rsi_max = st.sidebar.slider("RSI上限（以下を抽出）", 10, 70, 30)

st.sidebar.header("🔔 GC予兆フィルター")
gc_days_max = st.sidebar.slider("GC予測まで何営業日以内？", 5, 30, 15)
gc_only = st.sidebar.checkbox("GC予兆銘柄のみ表示", value=False)

st.sidebar.header("📋 ウォッチリスト")

# 日経225プリセットボタン
if st.sidebar.button("📊 日経225全銘柄をセット"):
    st.session_state["tickers_input"] = NIKKEI225

default_tickers = "7203.T\n6758.T\n9984.T\n6861.T\n8306.T\n7974.T\n6902.T\n9432.T"
tickers_input = st.sidebar.text_area(
    "銘柄コードを1行ずつ入力（.T = 東証）",
    value=st.session_state.get("tickers_input", default_tickers),
    height=200,
    key="tickers_input"
)

if st.button("🔍 スクリーニング実行", type="primary"):
    tickers = [t.strip() for t in tickers_input.strip().split("\n") if t.strip()]
    results = []
    progress = st.progress(0)
    status = st.empty()

    for i, ticker in enumerate(tickers):
        status.text(f"取得中: {ticker} ({i+1}/{len(tickers)})")
        progress.progress((i + 1) / len(tickers))
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period="6mo")
            if hist.empty or len(hist) < 15:
                continue
            hist = hist.dropna(subset=["Close", "Volume"])
            if len(hist) < 15:
                continue
            hist["RSI"] = ta.momentum.RSIIndicator(hist["Close"], window=14).rsi()
            rsi_val = safe_float(hist["RSI"].iloc[-1])
            close_val = safe_float(hist["Close"].iloc[-1])
            volume_val = safe_float(hist["Volume"].iloc[-1])
            if rsi_val is None or close_val is None:
                continue
            gap_pct, slope, est_days = detect_gc_sign(hist)
            if gap_pct is not None:
                gc_label = f"⚡ 約{est_days}日後" if est_days else "📈 接近中"
            else:
                gc_label = "-"
            info = stock.info
            per = safe_float(info.get("trailingPE") or info.get("forwardPE"))
            pbr = safe_float(info.get("priceToBook"))
            results.append({
                "銘柄コード": ticker,
                "銘柄名": info.get("longName") or info.get("shortName") or ticker,
                "株価(円)": round(close_val),
                "RSI": round(rsi_val, 1),
                "GC予兆": gc_label,
                "乖離率(%)": gap_pct if gap_pct else "-",
                "縮小スピード": slope if slope else "-",
                "PER": round(per, 1) if per else "N/A",
                "PBR": round(pbr, 2) if pbr else "N/A",
                "出来高": int(volume_val) if volume_val else 0,
            })
        except Exception:
            continue

    status.empty()
    progress.empty()

    if not results:
        st.warning("データを取得できませんでした。")
    else:
        df = pd.DataFrame(results)
        if gc_only:
            df = df[df["GC予兆"] != "-"]

        st.subheader("📊 全銘柄一覧")
        st.dataframe(df, use_container_width=True)

        st.subheader(f"🎯 RSI {rsi_max}以下の銘柄")
        hit = df[df["RSI"] <= rsi_max]
        if hit.empty:
            st.info("条件に一致する銘柄はありませんでした。条件を緩めてみてください。")
        else:
            st.success(f"{len(hit)}銘柄が条件に一致しました！")
            st.dataframe(hit, use_container_width=True)

        st.subheader(f"⚡ GC予兆銘柄（{gc_days_max}営業日以内）")
        gc_hit = df[df["GC予兆"] != "-"]
        if gc_hit.empty:
            st.info("GC予兆銘柄はありませんでした。")
        else:
            st.success(f"{len(gc_hit)}銘柄にGC予兆あり！")
            st.dataframe(gc_hit, use_container_width=True)