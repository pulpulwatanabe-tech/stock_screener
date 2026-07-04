import streamlit as st
import yfinance as yf
import pandas as pd
import ta
import math

st.set_page_config(page_title="株スクリーニングツール", page_icon="📈", layout="wide")
st.title("📈 株スクリーニングツール")
st.caption("RSIで割安株を自動抽出 ＋ ゴールデンクロス予兆検知")

# 日本語銘柄名辞書
JP_NAMES = {
    "1332.T": "ニッスイ", "1605.T": "INPEX", "1721.T": "コムシスHD",
    "1801.T": "大成建設", "1802.T": "大林組", "1803.T": "清水建設",
    "1808.T": "長谷工コーポレーション", "1812.T": "鹿島建設", "1925.T": "大和ハウス工業",
    "1928.T": "積水ハウス", "1963.T": "日揮HD", "2002.T": "日清製粉グループ本社",
    "2269.T": "明治HD", "2282.T": "日本ハム", "2413.T": "エムスリー",
    "2432.T": "ディー・エヌ・エー", "2501.T": "サッポロHD", "2502.T": "アサヒグループHD",
    "2503.T": "キリンHD", "2531.T": "宝HD", "2768.T": "双日",
    "2801.T": "キッコーマン", "2802.T": "味の素", "2871.T": "ニチレイ",
    "2914.T": "日本たばこ産業", "3086.T": "Jフロントリテイリング", "3092.T": "ZOZO",
    "3099.T": "三越伊勢丹HD", "3289.T": "東急不動産HD", "3382.T": "セブン＆アイHD",
    "3401.T": "帝人", "3402.T": "東レ", "3405.T": "クラレ",
    "3407.T": "旭化成", "3436.T": "SUMCO", "3659.T": "ネクソン",
    "3861.T": "王子HD", "3863.T": "日本製紙", "4004.T": "レゾナック・HD",
    "4005.T": "住友化学", "4021.T": "日産化学", "4042.T": "東ソー",
    "4043.T": "トクヤマ", "4061.T": "デンカ", "4063.T": "信越化学工業",
    "4151.T": "協和キリン", "4183.T": "三井化学", "4188.T": "三菱ケミカルグループ",
    "4202.T": "ダイセル", "4204.T": "積水化学工業", "4208.T": "UBE",
    "4324.T": "電通グループ", "4452.T": "花王", "4502.T": "武田薬品工業",
    "4503.T": "アステラス製薬", "4506.T": "住友ファーマ", "4507.T": "塩野義製薬",
    "4519.T": "中外製薬", "4523.T": "エーザイ", "4543.T": "テルモ",
    "4568.T": "第一三共", "4578.T": "大塚HD", "4661.T": "オリエンタルランド",
    "4689.T": "LINEヤフー", "4704.T": "トレンドマイクロ", "4751.T": "サイバーエージェント",
    "4755.T": "楽天グループ", "4901.T": "富士フイルムHD", "4902.T": "コニカミノルタ",
    "4911.T": "資生堂", "5001.T": "ENEOSホールディングス", "5002.T": "昭和シェル石油",
    "5019.T": "出光興産", "5020.T": "ENEOSホールディングス", "5101.T": "横浜ゴム",
    "5105.T": "TOYO TIRE", "5108.T": "ブリヂストン", "5201.T": "AGC",
    "5202.T": "日本板硝子", "5214.T": "日本電気硝子", "5232.T": "住友大阪セメント",
    "5233.T": "太平洋セメント", "5301.T": "東海カーボン", "5332.T": "TOTO",
    "5333.T": "日本ガイシ", "5401.T": "日本製鉄", "5406.T": "神戸製鋼所",
    "5411.T": "JFEホールディングス", "5413.T": "日新製鋼", "5541.T": "大平洋金属",
    "5631.T": "日本製鋼所", "5703.T": "日本軽金属HD", "5706.T": "三井金属鉱業",
    "5711.T": "三菱マテリアル", "5713.T": "住友金属鉱山", "5714.T": "DOWAホールディングス",
    "5715.T": "古河機械金属", "5801.T": "古河電気工業", "5802.T": "住友電気工業",
    "5803.T": "フジクラ", "6022.T": "赤阪鐵工所", "6098.T": "リクルートHD",
    "6103.T": "オークマ", "6113.T": "アマダ", "6146.T": "ディスコ",
    "6178.T": "日本郵政", "6273.T": "SMC", "6301.T": "小松製作所",
    "6302.T": "住友重機械工業", "6305.T": "日立建機", "6326.T": "クボタ",
    "6361.T": "荏原製作所", "6367.T": "ダイキン工業", "6370.T": "栗田工業",
    "6371.T": "椿本チエイン", "6395.T": "タダノ", "6412.T": "平和",
    "6417.T": "SANKYO", "6471.T": "日本精工", "6472.T": "NTN",
    "6473.T": "ジェイテクト", "6501.T": "日立製作所", "6503.T": "三菱電機",
    "6504.T": "富士電機", "6506.T": "安川電機", "6526.T": "ソシオネクスト",
    "6586.T": "マキタ", "6594.T": "日本電産", "6645.T": "オムロン",
    "6674.T": "GSユアサ", "6701.T": "日本電気", "6702.T": "富士通",
    "6703.T": "沖電気工業", "6724.T": "セイコーエプソン", "6752.T": "パナソニックHD",
    "6753.T": "シャープ", "6754.T": "アンリツ", "6758.T": "ソニーグループ",
    "6762.T": "TDK", "6770.T": "アルプスアルパイン", "6806.T": "ヒロセ電機",
    "6841.T": "横河電機", "6857.T": "アドバンテスト", "6861.T": "キーエンス",
    "6902.T": "デンソー", "6920.T": "レーザーテック", "6952.T": "カシオ計算機",
    "6954.T": "ファナック", "6963.T": "ローム", "6971.T": "京セラ",
    "6976.T": "太陽誘電", "6981.T": "村田製作所", "7003.T": "三井E&S",
    "7004.T": "日立造船", "7011.T": "三菱重工業", "7012.T": "川崎重工業",
    "7013.T": "IHI", "7186.T": "コンコルディアFG", "7201.T": "日産自動車",
    "7202.T": "いすゞ自動車", "7203.T": "トヨタ自動車", "7205.T": "日野自動車",
    "7211.T": "三菱自動車工業", "7261.T": "マツダ", "7267.T": "本田技研工業",
    "7269.T": "スズキ", "7270.T": "SUBARU", "7272.T": "ヤマハ発動機",
    "7731.T": "ニコン", "7733.T": "オリンパス", "7735.T": "SCREENホールディングス",
    "7741.T": "HOYA", "7751.T": "キヤノン", "7752.T": "リコー",
    "7762.T": "シチズン時計", "7832.T": "バンダイナムコHD", "7911.T": "凸版印刷",
    "7912.T": "大日本印刷", "7951.T": "ヤマハ", "7974.T": "任天堂",
    "8001.T": "伊藤忠商事", "8002.T": "丸紅", "8003.T": "トーメンデバイス",
    "8015.T": "豊田通商", "8031.T": "三井物産", "8035.T": "東京エレクトロン",
    "8053.T": "住友商事", "8056.T": "日立ハイテク", "8058.T": "三菱商事",
    "8233.T": "高島屋", "8252.T": "丸井グループ", "8253.T": "クレディセゾン",
    "8267.T": "イオン", "8303.T": "新生銀行", "8304.T": "あおぞら銀行",
    "8306.T": "三菱UFJフィナンシャルG", "8308.T": "りそなHD", "8309.T": "三井住友トラストHD",
    "8316.T": "三井住友フィナンシャルG", "8354.T": "ふくおかFG", "8355.T": "静岡銀行",
    "8411.T": "みずほフィナンシャルG", "8601.T": "大和証券グループ本社", "8604.T": "野村HD",
    "8630.T": "SOMPOホールディングス", "8697.T": "日本取引所グループ", "8725.T": "MS&ADインシュアランスG",
    "8750.T": "第一生命HD", "8766.T": "東京海上HD", "8795.T": "T&Dホールディングス",
    "9001.T": "東武鉄道", "9005.T": "東急", "9007.T": "小田急電鉄",
    "9008.T": "京王電鉄", "9009.T": "京成電鉄", "9020.T": "東日本旅客鉄道",
    "9021.T": "西日本旅客鉄道", "9022.T": "東海旅客鉄道", "9064.T": "ヤマトHD",
    "9101.T": "日本郵船", "9104.T": "商船三井", "9107.T": "川崎汽船",
    "9147.T": "NIPPON EXPRESSホールディングス", "9201.T": "日本航空", "9202.T": "ANAホールディングス",
    "9301.T": "三菱倉庫", "9432.T": "日本電信電話", "9433.T": "KDDI",
    "9434.T": "ソフトバンク", "9501.T": "東京電力HD", "9502.T": "中部電力",
    "9503.T": "関西電力", "9531.T": "東京ガス", "9532.T": "大阪ガス",
    "9602.T": "東宝", "9613.T": "NTTデータグループ", "9735.T": "セコム",
    "9766.T": "コナミグループ", "9983.T": "ファーストリテイリング", "9984.T": "ソフトバンクグループ",
}

# 日経225全銘柄
NIKKEI225 = "\n".join(JP_NAMES.keys())

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

            # 日本語名を辞書から取得、なければ英語名
            jp_name = JP_NAMES.get(ticker) or info.get("longName") or info.get("shortName") or ticker

            results.append({
                "銘柄コード": ticker,
                "銘柄名": jp_name,
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