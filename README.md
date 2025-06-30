# 📈 MarketPulse – Seasonal Stock Advisor

MarketPulse is a smart, modern stock analysis app that combines:
- 📅 Seasonal price patterns
- 📊 Technical indicators (RSI, Moving Average)
- 🧠 Sentiment analysis from **news** and **Reddit**
- 🗂️ Portfolio building + saving
- 📄 PDF reporting + 📧 email delivery

---

## 🌐 Try It Live
> [Launch App on Streamlit →](https://marketpulse.streamlit.app)

---

## 📸 Features

### ✅ Home Screen
Animated background of major stock logos

### ✅ Stock Analysis
- Enter a ticker (e.g., `AAPL`, `TSLA`)
- See RSI, MA50, and monthly seasonality
- View real-time sentiment from Yahoo Finance & Reddit

### ✅ Portfolio Builder
- Add multiple stocks
- Save and load your custom watchlist
- Export to CSV or JSON

### ✅ PDF Reports
- Generate branded reports (with charts + sentiment)
- Download or send via Gmail

---

## 🛠️ Tech Stack
- **Frontend**: Streamlit
- **Backend**: Python, yfinance, vaderSentiment, praw
- **Charts**: Matplotlib
- **PDF**: fpdf2
- **Email**: SMTP + Gmail App Password

---

## 🚀 Deploy It Yourself
```bash
pip install -r requirements.txt
streamlit run app.py
