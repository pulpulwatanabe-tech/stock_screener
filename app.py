import streamlit as st
import yfinance as yf
import pandas as pd
import ta
import math

st.set_page_config(page_title="株スクリーニングツール", page_icon="📈", layout="wide")
st.title("📈 株スクリーニングツール")
st.caption("RSIで割安株を自動抽出")

def safe_float(val):
    try:
        f = float(val)
        if math.isnan(f):
            return None
        return f
    except:
        return None

st.sidebar.header("⚙️ スクリーニング条件")
rsi_max = st.sidebar.slider("RSI上限（以下を抽出）", 10, 70, 30)

st.sidebar.header("📋 ウォッチリスト")
default_tickers = "7203.T\n6758.T\n9984.T\n6861.T\n8306.T\n7974.T\n6902.T\n9432.T"
tickers_input = st.sidebar.text_area(
    "銘柄コードを1行ずつ入力（.T = 東証）",
    value=default_tickers,
    height=200
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
            hist = stock.history(period="3mo")
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
            info = stock.info
            per = safe_float(info.get("trailingPE") or info.get("forwardPE"))
            pbr = safe_float(info.get("priceToBook"))
            results.append({
                "銘柄コード": ticker,
                "銘柄名": info.get("longName") or info.get("shortName") or ticker,
                "株価(円)": round(close_val),
                "RSI": round(rsi_val, 1),
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
        st.subheader("📊 全銘柄一覧")
        st.dataframe(df, use_container_width=True)

        st.subheader(f"🎯 RSI {rsi_max}以下の銘柄")
        hit = df[df["RSI"] <= rsi_max]
        if hit.empty:
            st.info("条件に一致する銘柄はありませんでした。条件を緩めてみてください。")
        else:
            st.success(f"{len(hit)}銘柄が条件に一致しました！")
            st.dataframe(hit, use_container_width=True)
