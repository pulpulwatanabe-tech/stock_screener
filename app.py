import streamlit as st
import yfinance as yf
import pandas as pd
import ta
import math

st.set_page_config(page_title="株スクリーニングツール", page_icon="📈", layout="wide")
st.title("📈 株スクリーニングツール")
st.caption("RSIで割安株を自動抽出 ＋ ゴールデンクロス予兆検知")

def safe_float(val):
    try:
        f = float(val)
        if math.isnan(f):
            return None
        return f
    except:
        return None

def detect_gc_sign(hist, short_window=25, long_window=75):
    """ゴールデンクロス予兆を検出する関数"""
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

    # 直近5日の乖離率の変化（縮小スピード）
    recent = hist["gap_pct"].tail(5)
    slope = safe_float(recent.iloc[-1] - recent.iloc[0])
    if slope is None:
        return None, None, None

    # 短期線がまだ長期線の下 かつ 縮小傾向
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
            hist = stock.history(period="6mo")  # GC計算のため6ヶ月に延長
            if hist.empty or len(hist) < 15:
                continue
            hist = hist.dropna(subset=["Close", "Volume"])
            if len(hist) < 15:
                continue

            # RSI計算
            hist["RSI"] = ta.momentum.RSIIndicator(hist["Close"], window=14).rsi()
            rsi_val = safe_float(hist["RSI"].iloc[-1])
            close_val = safe_float(hist["Close"].iloc[-1])
            volume_val = safe_float(hist["Volume"].iloc[-1])
            if rsi_val is None or close_val is None:
                continue

            # GC予兆計算
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

        # GC予兆フィルター適用
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