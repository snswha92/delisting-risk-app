import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta

# 폰트 설정
plt.rcParams['font.family'] = 'Arial'
plt.rcParams['axes.unicode_minus'] = False

# 분석 함수 정의
def analyze_stock_with_market_cap(ticker):
    stock = yf.Ticker(ticker)
    hist = stock.history(period='60d')
    hist = hist.tail(30)
    info = stock.info

    shares_outstanding = info.get("sharesOutstanding", None)

    if shares_outstanding is None or hist.empty or len(hist) < 30:
        st.error(f"{ticker}: Unable to retrieve sufficient data. (Less than 30 trading days)")
        return None

    hist = hist[['Close']].copy()
    hist['Date'] = hist.index
    hist.reset_index(drop=True, inplace=True)
    hist['Calculated Market Cap'] = hist['Close'] * shares_outstanding
    hist['Below_1'] = hist['Close'] < 1.0
    hist['Below_35M'] = hist['Calculated Market Cap'] < 35_000_000

    low_price_days = hist['Below_1'].sum()
    low_marketcap_days = hist['Below_35M'].sum()
    remain_price_days = max(0, 30 - low_price_days)
    remain_marketcap_days = max(0, 30 - low_marketcap_days)

    # 평가
    if low_price_days >= 30 and low_marketcap_days >= 30:
        level = "🔴"
        color = "red"
        risk_statement = "High risk of delisting."
    elif low_price_days >= 30:
        level = "🔴"
        color = "red"
        risk_statement = "Price criterion alone poses delisting risk."
    elif low_marketcap_days >= 30:
        level = "🔴"
        color = "darkred"
        risk_statement = "Market cap criterion alone poses delisting risk."
    elif low_price_days >= 21 or low_marketcap_days >= 21:
        level = "🟠"
        color = "orange"
        risk_statement = "Warning: Approaching delisting threshold."
    elif low_price_days >= 14 or low_marketcap_days >= 14:
        level = "🟡"
        color = "gold"
        risk_statement = "Caution: Maintain compliance."
    else:
        level = "✅"
        color = "green"
        risk_statement = "This stock is currently safe from delisting."

    delisting_note = ""
    today = datetime.now().date()
    if low_price_days >= 14 or low_marketcap_days >= 14:
        remaining_days = int(remain_price_days if low_price_days >= 14 else remain_marketcap_days)
        estimated_date = today + timedelta(days=remaining_days)
        delisting_note = f"\n⚠ Potential delisting date: **{estimated_date.strftime('%Y-%m-%d')}**"

    # 그래프 생성
    fig = plt.figure(figsize=(14, 10))
    gs = fig.add_gridspec(2, 2, height_ratios=[3, 1])

    # 가격 그래프
    ax1 = fig.add_subplot(gs[0, 0])
    ax1.plot(hist['Date'], hist['Close'], linestyle='-', marker='o', color='blue', label='Closing Price ($)')
    ax1.axhline(1.0, color='red', linestyle='-', linewidth=1.2, label='Price Threshold ($1)')
    ax1.set_ylabel("Closing Price ($)", color='blue')
    ax1.tick_params(axis='y', labelcolor='blue')
    ax1.xaxis.set_major_locator(mdates.DayLocator(interval=7))
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
    ax1.set_title(f"{ticker} Price Trend")
    ax1.legend(loc='upper left')

    # 시가총액 그래프
    ax2 = fig.add_subplot(gs[0, 1])
    ax2.plot(hist['Date'], hist['Calculated Market Cap'] / 1e6, linestyle='-', marker='o', linewidth=1.5, color='purple', label='Market Cap (Million $)')
    ax2.axhline(35, color='crimson', linestyle='-', linewidth=1.2, label='Cap Threshold ($35M)')
    ax2.set_ylabel("Market Cap (Million $)", color='purple')
    ax2.tick_params(axis='y', labelcolor='purple')
    ax2.xaxis.set_major_locator(mdates.DayLocator(interval=7))
    ax2.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
    ax2.set_title(f"{ticker} Market Cap Trend")
    ax2.legend(loc='upper left')

    # 메시지 박스
    ax3 = fig.add_subplot(gs[1, :])
    ax3.axis('off')
    message = (
        f"📊 {ticker} Risk Assessment:\n"
        f"- Shares Outstanding: {shares_outstanding:,}\n"
        f"- Days below $1: {low_price_days} (Remaining: {remain_price_days})\n"
        f"- Days below $35M Market Cap: {low_marketcap_days} (Remaining: {remain_marketcap_days})\n"
        f"- Status: {risk_statement}" + delisting_note
    )
    ax3.text(0.5, 0.5, message, ha='center', va='center', fontsize=13, color=color, bbox=dict(facecolor='aliceblue', alpha=0.9))

    plt.suptitle(f"{ticker} Price & Market Cap Trend and Delisting Risk", fontsize=16, color=color)
    plt.tight_layout(rect=[0, 0.05, 1, 0.95])
    st.pyplot(fig)

    return hist[['Date', 'Close', 'Calculated Market Cap']]

# Streamlit 앱 시작
st.set_page_config(page_title="Delisting Risk Analyzer", layout="wide")
st.title("📉 Delisting Risk Analyzer")
st.write("티커를 입력하면 최근 30거래일 기준 상장폐지 위험을 분석합니다.")

ticker_input = st.text_input("Enter stock ticker (e.g., AMC)", value="")

if st.button("Analyze"):
    if ticker_input:
        df_result = analyze_stock_with_market_cap(ticker_input.upper())
        if df_result is not None:
            st.markdown("### 📋 Recent 30-Day Data")
            df_result.columns = ['Date', 'Close ($)', 'Market Cap ($)']
            st.dataframe(df_result)
    else:
        st.warning("티커를 입력해주세요.")
