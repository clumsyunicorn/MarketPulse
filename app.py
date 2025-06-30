import streamlit as st
import os
import yfinance as yf
import pandas as pd
import json
import datetime
import matplotlib.pyplot as plt
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from utils.sentiment_analysis import (
    get_yahoo_finance_headlines,
    analyze_sentiment,
    summarize_sentiment
)

email = st.secrets["GMAIL_USER"]
st.set_page_config(page_title="MarketPulse", layout="wide")

def load_landing_animation():
    with open("templates/floating_icons.html", "r", encoding="utf-8") as f:
        st.components.v1.html(f.read(), height=800, scrolling=False)

st.sidebar.title("📊 MarketPulse Navigation")
section = st.sidebar.radio("Go to", ["Home", "Stock Analysis", "Portfolio", "Reports"])

# HOME TAB
if section == "Home":
    st.markdown("## 🌐 Welcome to MarketPulse")
    st.write("A clean, modern stock advisor using sentiment + seasonality.")
    load_landing_animation()

# STOCK ANALYSIS TAB
elif section == "Stock Analysis":
    st.title("📈 Stock Timing Analysis")

    ticker = st.text_input("Enter a stock ticker:", value="AAPL").upper()
    today = datetime.date.today()
    start_date = st.date_input("Start Date", today - datetime.timedelta(days=365 * 5))
    end_date = st.date_input("End Date", today)

    if st.button("Run Analysis"):
        with st.spinner("Fetching and analyzing..."):
            try:
                data = yf.download(ticker, start=start_date, end=end_date)
                if data.empty:
                    st.error("No data found.")
                else:
                    data['Return'] = data['Adj Close'].pct_change()
                    data['Month'] = data.index.month_name()
                    data['RSI'] = 100 - (100 / (1 + data['Return'].rolling(14).mean() / data['Return'].rolling(14).std()))
                    data['MA50'] = data['Adj Close'].rolling(window=50).mean()

                    monthly_returns = data.groupby('Month')['Return'].mean().reindex([
                        'January', 'February', 'March', 'April', 'May', 'June',
                        'July', 'August', 'September', 'October', 'November', 'December'
                    ])

                    st.subheader("📊 Monthly Returns")
                    st.bar_chart(monthly_returns)

                    st.subheader("📉 Price + MA50")
                    st.line_chart(data[['Adj Close', 'MA50']].dropna())

                    st.subheader("📌 RSI")
                    st.line_chart(data[['RSI']].dropna())

                    # Save charts
                    fig_rsi, ax = plt.subplots()
                    data['RSI'].dropna().plot(ax=ax, title=f"{ticker} RSI")
                    fig_rsi.savefig(f"reports/{ticker}_rsi.png")

                    fig_ma, ax2 = plt.subplots()
                    data[['Adj Close', 'MA50']].dropna().plot(ax=ax2, title=f"{ticker} Price + MA50")
                    fig_ma.savefig(f"reports/{ticker}_ma.png")

                    csv = data.to_csv().encode('utf-8')
                    st.download_button("Download CSV", csv, file_name=f"{ticker}_data.csv")

                    # Yahoo Sentiment
                    st.subheader("🧠 News Sentiment")
                    headlines = get_yahoo_finance_headlines(ticker)
                    if headlines:
                        results = analyze_sentiment(headlines)
                        avg, label = summarize_sentiment(results)

                        col1, col2 = st.columns(2)
                        col1.metric("Avg Sentiment", avg)
                        col2.metric("Tone", label)
                        emoji = "🟢" if label == "Positive" else "🔴" if label == "Negative" else "⚪"
                        st.markdown(f"#### Sentiment Gauge: {emoji} {label}")
                        for r in results:
                            e = "🟢" if r["label"] == "Positive" else "🔴" if r["label"] == "Negative" else "⚪"
                            st.write(f"{e} **{r['headline']}** ({r['score']})")
                    else:
                        st.warning("No news headlines.")

                    # Reddit Sentiment
                    st.subheader("🧵 Reddit Sentiment (Optional)")
                    rid = st.text_input("Reddit client_id")
                    rsecret = st.text_input("Reddit client_secret")
                    if rid and rsecret:
                        from utils.sentiment_analysis import get_reddit_headlines
                        reddit_headlines = get_reddit_headlines(ticker, rid, rsecret)
                        if reddit_headlines:
                            results = analyze_sentiment(reddit_headlines)
                            avg, label = summarize_sentiment(results)
                            st.metric("Reddit Tone", label)
                            for r in results:
                                emoji = "🟢" if r["label"] == "Positive" else "🔴" if r["label"] == "Negative" else "⚪"
                                st.write(f"{emoji} {r['headline']} ({r['score']})")

            except Exception as e:
                st.error(f"Error: {e}")

# PORTFOLIO TAB
elif section == "Portfolio":
    st.title("📁 Portfolio Builder")

    if "portfolio" not in st.session_state:
        st.session_state.portfolio = []

    ticker_input = st.text_input("Add stock to portfolio:").upper()
    start = st.date_input("Start", datetime.date(2022, 1, 1))
    end = st.date_input("End", datetime.date.today())

    if st.button("Add to Portfolio"):
        if ticker_input:
            st.session_state.portfolio.append({
                "ticker": ticker_input,
                "start": str(start),
                "end": str(end)
            })
            st.success(f"{ticker_input} added!")

    st.subheader("📋 Current Portfolio")
    if st.session_state.portfolio:
        df = pd.DataFrame(st.session_state.portfolio)
        st.dataframe(df)
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("Download Portfolio CSV", csv, "portfolio.csv")

        if st.button("💾 Save Portfolio"):
            os.makedirs("reports", exist_ok=True)
            with open("reports/portfolio_plan.json", "w") as f:
                json.dump(st.session_state.portfolio, f)
            st.success("Saved!")

        if os.path.exists("reports/portfolio_plan.json") and st.button("📤 Load Saved Plan"):
            with open("reports/portfolio_plan.json", "r") as f:
                st.session_state.portfolio = json.load(f)
            st.success("Loaded!")

    else:
        st.info("No stocks added yet.")

# REPORT TAB
elif section == "Reports":
    from utils.report_generator import PDF
    from utils.email_report import send_report_via_email

    st.title("📄 Generate Report")

    if "portfolio" not in st.session_state or not st.session_state.portfolio:
        st.warning("Portfolio is empty.")
    else:
        if st.button("🖨️ Generate PDF"):
            pdf = PDF()
            pdf.add_page()

            for stock in st.session_state.portfolio:
                ticker = stock["ticker"]
                start = stock["start"]
                end = stock["end"]
                headlines = get_yahoo_finance_headlines(ticker)
                if headlines:
                    results = analyze_sentiment(headlines)
                    avg, label = summarize_sentiment(results)
                else:
                    avg, label = 0, "Neutral"

                pdf.add_stock_section(ticker, label, avg)
                pdf.add_text(f"Timeframe: {start} to {end}")

            os.makedirs("reports", exist_ok=True)
            path = "reports/marketpulse_report.pdf"
            pdf.save(path)

            with open(path, "rb") as f:
                st.download_button("📥 Download PDF", f, file_name="MarketPulse_Report.pdf", mime="application/pdf")

        st.subheader("📧 Email Report")
        sender = st.text_input("Your Gmail")
        app_pw = st.text_input("App Password", type="password")
        recipient = st.text_input("Send to Email")

        if st.button("Send Email"):
            try:
                send_report_via_email(sender, app_pw, recipient, "reports/marketpulse_report.pdf")
                st.success("Sent!")
            except Exception as e:
                st.error(f"Failed: {e}")
