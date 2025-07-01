
import streamlit as st
import os
import yfinance as yf
import pandas as pd
import json
import datetime
import matplotlib.pyplot as plt
import numpy as np
import requests
from bs4 import BeautifulSoup
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from fpdf import FPDF

# Page config
st.set_page_config(
    page_title="MarketPulse - Smart Stock Advisor", 
    layout="wide",
    initial_sidebar_state="collapsed",
    page_icon="💰"
)

# Initialize session state
if "current_page" not in st.session_state:
    st.session_state.current_page = "home"
if "portfolio" not in st.session_state:
    st.session_state.portfolio = []

# Modern CSS for young adults (20s) - inviting colors
# Custom CSS for hip homepage design with floating animations
st.markdown("""
<style>
    /* Global Styles */
    .stApp {
        background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #ec4899 100%);
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Floating Stock Animations */
    .floating-container {
        position: fixed;
        top: 0;
        left: 0;
        width: 100vw;
        height: 100vh;
        overflow: hidden;
        z-index: -1;
        pointer-events: none;
    }
    
    .floating-ticker {
        position: absolute;
        width: 70px;
        height: 70px;
        border-radius: 20px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: bold;
        font-size: 12px;
        color: white;
        text-shadow: 0 2px 4px rgba(0,0,0,0.3);
        box-shadow: 0 8px 32px rgba(0,0,0,0.2);
        backdrop-filter: blur(4px);
        border: 1px solid rgba(255,255,255,0.3);
    }
    
    /* Waterfall animation */
    @keyframes waterfall {
        0% { 
            transform: translateY(-100px) rotate(0deg); 
            opacity: 0; 
        }
        10% { 
            opacity: 0.8; 
        }
        90% { 
            opacity: 0.8; 
        }
        100% { 
            transform: translateY(100vh) rotate(360deg); 
            opacity: 0; 
        }
    }
    
    .waterfall-1 { animation: waterfall 12s linear infinite; }
    .waterfall-2 { animation: waterfall 15s linear infinite; }
    .waterfall-3 { animation: waterfall 18s linear infinite; }
    
    /* Navigation */
    .nav-container {
        background: rgba(255,255,255,0.15);
        backdrop-filter: blur(20px);
        border-radius: 20px;
        padding: 1rem 2rem;
        margin: 1rem 0;
        border: 1px solid rgba(255,255,255,0.2);
        box-shadow: 0 8px 32px rgba(0,0,0,0.1);
    }
    
    /* Page Container */
    .page-container {
        background: rgba(255,255,255,0.1);
        backdrop-filter: blur(20px);
        border-radius: 25px;
        padding: 2rem;
        margin: 1rem 0;
        border: 1px solid rgba(255,255,255,0.2);
        box-shadow: 0 8px 32px rgba(0,0,0,0.1);
        min-height: 80vh;
    }
    
    /* Hero Section */
    .hero-title {
        font-size: 4rem;
        font-weight: 900;
        text-align: center;
        margin-bottom: 1rem;
        background: linear-gradient(45deg, #f59e0b, #eab308);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-shadow: 0 4px 8px rgba(0,0,0,0.3);
    }
    
    .hero-subtitle {
        font-size: 1.3rem;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
        font-weight: 300;
    }
    
    /* Feature Cards */
    .feature-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
        gap: 2rem;
        margin: 2rem 0;
    }
    
    .feature-card {
        background: rgba(255,255,255,0.15);
        backdrop-filter: blur(15px);
        border-radius: 20px;
        padding: 2rem;
        text-align: center;
        border: 1px solid rgba(255,255,255,0.3);
        transition: all 0.3s ease;
    }
    
    .feature-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 15px 35px rgba(0,0,0,0.2);
        background: rgba(255,255,255,0.2);
    }
    
    .feature-icon {
        font-size: 3rem;
        margin-bottom: 1rem;
    }
    
    .feature-title {
        font-size: 1.4rem;
        font-weight: bold;
        color: white;
        margin-bottom: 1rem;
    }
    
    .feature-description {
        color: rgba(255,255,255,0.9);
        line-height: 1.6;
    }
    
    /* Buttons */
    .action-buttons {
        display: flex;
        gap: 1rem;
        justify-content: center;
        margin: 2rem 0;
        flex-wrap: wrap;
    }
    
    .cta-button {
        background: linear-gradient(45deg, #f59e0b, #eab308);
        color: white;
        padding: 1rem 2rem;
        border-radius: 50px;
        border: none;
        font-weight: bold;
        font-size: 1.1rem;
        cursor: pointer;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(245, 158, 11, 0.3);
        text-decoration: none;
    }
    
    .cta-button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(245, 158, 11, 0.4);
    }
    
    /* Metric Cards */
    .metric-card {
        background: rgba(255,255,255,0.15);
        backdrop-filter: blur(15px);
        border-radius: 15px;
        padding: 1.5rem;
        text-align: center;
        border: 1px solid rgba(255,255,255,0.3);
        margin: 0.5rem 0;
    }
    
    /* Input Styling */
    .stTextInput > div > div > input {
        background: rgba(255,255,255,0.9);
        border-radius: 15px;
        border: 1px solid rgba(255,255,255,0.3);
        padding: 0.75rem 1rem;
        font-size: 1rem;
    }
    
    .stSelectbox > div > div > select {
        background: rgba(255,255,255,0.9);
        border-radius: 15px;
        border: 1px solid rgba(255,255,255,0.3);
    }
    
    /* Button Styling */
    .stButton > button {
        background: linear-gradient(45deg, #6366f1, #8b5cf6);
        color: white;
        border-radius: 25px;
        border: none;
        padding: 0.75rem 1.5rem;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(99, 102, 241, 0.3);
    }
    
    /* Success/Error Messages */
    .stSuccess {
        background: rgba(34, 197, 94, 0.2);
        border: 1px solid rgba(34, 197, 94, 0.3);
        border-radius: 15px;
    }
    
    /* Footer */
    .stError {
        background: rgba(239, 68, 68, 0.2);
        border: 1px solid rgba(239, 68, 68, 0.3);
        border-radius: 15px;
    }
    
    /* Responsive */
    @media (max-width: 768px) {
        .hero-title {
            font-size: 2.5rem;
        }
        
        .floating-ticker {
            width: 50px;
            height: 50px;
            font-size: 10px;
        }
    }
</style>
""", unsafe_allow_html=True)


def create_floating_tickers():
    """Create floating waterfall effect with stock tickers"""
    tickers = [
        {"symbol": "TSLA", "color": "#ef4444", "left": 5},
        {"symbol": "AMZN", "color": "#f97316", "left": 15},
        {"symbol": "GOOGL", "color": "#3b82f6", "left": 25},
        {"symbol": "MSFT", "color": "#06b6d4", "left": 35},
        {"symbol": "AAPL", "color": "#6366f1", "left": 45},
        {"symbol": "NFLX", "color": "#dc2626", "left": 55},
        {"symbol": "META", "color": "#8b5cf6", "left": 65},
        {"symbol": "NVDA", "color": "#10b981", "left": 75},
        {"symbol": "AMD", "color": "#f59e0b", "left": 85},
        {"symbol": "SPY", "color": "#84cc16", "left": 95},
    ]
    
    floating_html = '<div class="floating-container">'
    
    # Create multiple layers for full coverage
    for layer in range(3):
        for i, ticker in enumerate(tickers):
            animation_class = f"waterfall-{(i % 3) + 1}"
            delay = i * 1.5 + layer * 4
            left_pos = (ticker['left'] + layer * 3) % 100
            
            floating_html += f'''
            <div class="floating-ticker {animation_class}" 
                 style="left: {left_pos}%; 
                        background: {ticker['color']}; 
                        animation-delay: {delay}s;">
                {ticker['symbol']}
            </div>
            '''
    
    floating_html += '</div>'
    return floating_html

# Utility Functions
def get_yahoo_finance_headlines(ticker):
    """Get headlines from Yahoo Finance"""
    try:
        url = f"https://finance.yahoo.com/quote/{ticker}/news"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            headlines = []
            news_items = soup.find_all('h3', class_='Mb(5px)')
            for item in news_items[:10]:
                headline = item.get_text().strip()
                if headline:
                    headlines.append(headline)
            return headlines
        return []
    except Exception as e:
        return []


def analyze_sentiment(headlines):
    """Analyze sentiment of headlines"""
    analyzer = SentimentIntensityAnalyzer()
    results = []
    
    for headline in headlines:
        score = analyzer.polarity_scores(headline)
        compound = score['compound']
        
        if compound >= 0.05:
            label = "Positive"
        elif compound <= -0.05:
            label = "Negative"
        else:
            label = "Neutral"
            
        results.append({
            'headline': headline,
            'score': compound,
            'label': label
        })
    
    return results


def summarize_sentiment(results):
    """Summarize overall sentiment"""
    if not results:
        return 0, "Neutral"
    
    avg_score = sum(r['score'] for r in results) / len(results)
    
    if avg_score >= 0.05:
        label = "Positive"
    elif avg_score <= -0.05:
        label = "Negative"
    else:
        label = "Neutral"
    
    return avg_score, label


def calculate_technical_indicators(data):
    """Calculate comprehensive technical indicators"""
    # RSI
    delta = data['Adj Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    data['RSI'] = 100 - (100 / (1 + rs))
    
    # Moving Averages
    data['SMA_20'] = data['Adj Close'].rolling(window=20).mean()
    data['SMA_50'] = data['Adj Close'].rolling(window=50).mean()
    data['SMA_200'] = data['Adj Close'].rolling(window=200).mean()
    
    # EMA
    data['EMA_12'] = data['Adj Close'].ewm(span=12).mean()
    data['EMA_26'] = data['Adj Close'].ewm(span=26).mean()
    
    # MACD
    data['MACD'] = data['EMA_12'] - data['EMA_26']
    data['MACD_Signal'] = data['MACD'].ewm(span=9).mean()
    data['MACD_Histogram'] = data['MACD'] - data['MACD_Signal']
    
    # Bollinger Bands
    data['BB_Middle'] = data['Adj Close'].rolling(window=20).mean()
    std = data['Adj Close'].rolling(window=20).std()
    data['BB_Upper'] = data['BB_Middle'] + (std * 2)
    data['BB_Lower'] = data['BB_Middle'] - (std * 2)
    
    return data


class PDFReport(FPDF):
    def __init__(self):
        super().__init__()
        self.set_auto_page_break(auto=True, margin=15)
        
    def header(self):
        self.set_font('Arial', 'B', 15)
        self.cell(0, 10, 'MarketPulse - Portfolio Analysis Report', 0, 1, 'C')
        self.ln(10)
        
    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()} - Generated: {datetime.date.today()}', 0, 0, 'C')

# Add floating animation to all pages
st.markdown(create_floating_tickers(), unsafe_allow_html=True)

# Navigation
st.markdown('<div class="nav-container">', unsafe_allow_html=True)
col1, col2, col3, col4, col5 = st.columns([1, 1, 1, 1, 1])

with col1:
    if st.button("🏠 Home", key="nav_home", use_container_width=True):
        st.session_state.current_page = "home"
        st.rerun()

with col2:
    if st.button("📊 Analysis", key="nav_analysis", use_container_width=True):
        st.session_state.current_page = "analysis"
        st.rerun()

with col3:
    if st.button("💼 Portfolio", key="nav_portfolio", use_container_width=True):
        st.session_state.current_page = "portfolio"
        st.rerun()

with col4:
    if st.button("📈 Reports", key="nav_reports", use_container_width=True):
        st.session_state.current_page = "reports"
        st.rerun()

with col5:
    if st.button("ℹ️ About", key="nav_about", use_container_width=True):
        st.session_state.current_page = "about"
        st.rerun()

st.markdown('</div>', unsafe_allow_html=True)

# HOME PAGE
# Check if we're on the homepage
if st.session_state.current_page == "home":
    st.markdown('<div class="page-container">', unsafe_allow_html=True)
    
    # Hero Section
    # Add JavaScript for button functionality
    st.markdown("""
    <div class="hero-title">MarketPulse</div>
    <div class="hero-subtitle">Smart Stock Analysis for the Next Generation</div>
    """, unsafe_allow_html=True)
    
    # Quick Stock Lookup
    st.markdown("### 🚀 Quick Stock Analysis")
# Navigation logic (simplified for demo)
    col1, col2 = st.columns([3, 1])
    
    with col1:
        quick_ticker = st.text_input("Enter a stock ticker (e.g., AAPL, TSLA)", key="quick_ticker")
    
    with col2:
        if st.button("Analyze Now", key="quick_analyze", type="primary"):
            if quick_ticker:
                st.session_state.current_page = "analysis"
                st.session_state.selected_ticker = quick_ticker.upper()
                st.rerun()
    
    # Feature Cards
    st.markdown('<div class="feature-grid">', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon">🧠</div>
            <div class="feature-title">Smart Analysis</div>
            <div class="feature-description">
                AI-powered sentiment analysis combined with technical indicators 
                to give you the complete picture.
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon">⏰</div>
            <div class="feature-title">Perfect Timing</div>
            <div class="feature-description">
                Seasonal patterns and historical data help you find the best 
                times to buy and sell.
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon">📱</div>
            <div class="feature-title">Easy to Use</div>
            <div class="feature-description">
                No confusing jargon. Clean, simple interface designed 
                for beginners and pros alike.
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Action Buttons
    st.markdown('<div class="action-buttons">', unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📊 Start Analysis", key="start_analysis", use_container_width=True):
            st.session_state.current_page = "analysis"
            st.rerun()
    
    with col2:
        if st.button("💼 Build Portfolio", key="build_portfolio", use_container_width=True):
            st.session_state.current_page = "portfolio"
            st.rerun()
    
    with col3:
        if st.button("📈 View Reports", key="view_reports", use_container_width=True):
            st.session_state.current_page = "reports"
            st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ANALYSIS PAGE
elif st.session_state.current_page == "analysis":
    st.markdown('<div class="page-container">', unsafe_allow_html=True)
    st.title("📊 Stock Analysis")
    
    # Get ticker input
    if 'selected_ticker' in st.session_state:
        default_ticker = st.session_state.selected_ticker
    else:
        default_ticker = "AAPL"
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        ticker = st.text_input("Stock Ticker:", value=default_ticker).upper()
    
    with col2:
        period = st.selectbox("Time Period:", ["1y", "2y", "5y", "max"])
    
    if st.button("🚀 Run Analysis", type="primary", use_container_width=True):
        if ticker:
            with st.spinner("Analyzing stock data..."):
                try:
                    # Fetch data
                    data = yf.download(ticker, period=period)
                    
                    if data.empty:
                        st.error("❌ No data found for this ticker")
                    else:
                        # Calculate indicators
                        data = calculate_technical_indicators(data)
                        
                        # Current metrics
                        current_price = data['Adj Close'].iloc[-1]
                        current_rsi = data['RSI'].iloc[-1] if not pd.isna(data['RSI'].iloc[-1]) else 50
                        change = data['Adj Close'].pct_change().iloc[-1] * 100
                        
                        # Display metrics
                        col1, col2, col3, col4 = st.columns(4)
                        
                        with col1:
                            st.metric("💰 Price", f"${current_price:.2f}", f"{change:+.2f}%")
                        
                        with col2:
                            rsi_status = "Oversold" if current_rsi < 30 else "Overbought" if current_rsi > 70 else "Normal"
                            st.metric("📊 RSI", f"{current_rsi:.1f}", rsi_status)
                        
                        with col3:
                            sma_20 = data['SMA_20'].iloc[-1]
                            trend = "Above" if current_price > sma_20 else "Below"
                            st.metric("📈 SMA(20)", f"${sma_20:.2f}", trend)
                        
                        with col4:
                            # Simple recommendation
                            if current_rsi < 30:
                                recommendation = "BUY 🟢"
                            elif current_rsi > 70:
                                recommendation = "SELL 🔴"
                            else:
                                recommendation = "HOLD 🟡"
                            st.metric("🎯 Signal", recommendation)
                        
                        # Charts
                        st.subheader("📈 Price Chart")
                        chart_data = data[['Adj Close', 'SMA_20', 'SMA_50']].dropna()
                        st.line_chart(chart_data)
                        
                        st.subheader("📊 RSI Indicator")
                        st.line_chart(data['RSI'].dropna())
                        
                        # Sentiment Analysis
                        st.subheader("🧠 Market Sentiment")
                        
                        headlines = get_yahoo_finance_headlines(ticker)
                        
                        if headlines:
                            results = analyze_sentiment(headlines)
                            avg_sentiment, sentiment_label = summarize_sentiment(results)
                            
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                st.metric("📰 Sentiment", sentiment_label)
                            
                            with col2:
                                st.metric("📊 Score", f"{avg_sentiment:.3f}")
                            
                            # Show recent headlines
                            with st.expander("📰 Recent News"):
                                for result in results[:5]:
                                    emoji = "🟢" if result["label"] == "Positive" else "🔴" if result["label"] == "Negative" else "🟡"
                                    st.write(f"{emoji} {result['headline']}")
                        else:
                            st.info("No recent news found")
                        
                        # Add to portfolio button
                        if st.button("➕ Add to Portfolio", type="secondary"):
                            stock_data = {
                                "ticker": ticker,
                                "price": current_price,
                                "rsi": current_rsi,
                                "recommendation": recommendation,
                                "sentiment": sentiment_label if headlines else "N/A",
                                "added_date": str(datetime.date.today())
                            }
                            st.session_state.portfolio.append(stock_data)
                            st.success(f"✅ {ticker} added to portfolio!")
                
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
    
    st.markdown('</div>', unsafe_allow_html=True)

# PORTFOLIO PAGE
elif st.session_state.current_page == "portfolio":
    st.markdown('<div class="page-container">', unsafe_allow_html=True)
    st.title("💼 Your Portfolio")
    
    # Add stock section
    st.subheader("➕ Add New Stock")
    col1, col2 = st.columns([3, 1])
    
    with col1:
        new_ticker = st.text_input("Stock Ticker:", key="portfolio_ticker").upper()
    
    with col2:
        if st.button("Add Stock", type="primary", use_container_width=True):
            if new_ticker:
                try:
                    # Quick analysis
                    data = yf.download(new_ticker, period="1y")
                    if not data.empty:
                        current_price = data['Adj Close'].iloc[-1]
                        
                        # Calculate RSI
                        delta = data['Adj Close'].diff()
                        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
                        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                        rs = gain / loss
                        rsi = (100 - (100 / (1 + rs))).iloc[-1]
                        
                        recommendation = "BUY 🟢" if rsi < 30 else "SELL 🔴" if rsi > 70 else "HOLD 🟡"
                        
                        stock_data = {
                            "ticker": new_ticker,
                            "price": current_price,
                            "rsi": rsi,
                            "recommendation": recommendation,
                            "added_date": str(datetime.date.today())
                        }
                        
                        st.session_state.portfolio.append(stock_data)
                        st.success(f"✅ {new_ticker} added to portfolio!")
                        st.rerun()
                    else:
                        st.error("❌ Invalid ticker")
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
    
    # Display portfolio
    if st.session_state.portfolio:
        st.subheader("📊 Portfolio Overview")
        
        df = pd.DataFrame(st.session_state.portfolio)
        
        # Portfolio metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("📈 Total Stocks", len(df))
        
        with col2:
            buy_signals = len(df[df['recommendation'].str.contains('BUY', na=False)])
            st.metric("🟢 Buy Signals", buy_signals)
        
        with col3:
            sell_signals = len(df[df['recommendation'].str.contains('SELL', na=False)])
            st.metric("🔴 Sell Signals", sell_signals)
        
        with col4:
            avg_rsi = df['rsi'].mean()
            st.metric("📊 Avg RSI", f"{avg_rsi:.1f}")
        
        # Portfolio table
        st.dataframe(df, use_container_width=True)
        
        # Portfolio actions
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("💾 Save Portfolio", use_container_width=True):
                os.makedirs("reports", exist_ok=True)
                with open("reports/portfolio.json", "w") as f:
                    json.dump(st.session_state.portfolio, f, indent=2)
                st.success("✅ Portfolio saved!")
        
        with col2:
            csv_data = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                "📥 Download CSV",
                csv_data,
                file_name=f"portfolio_{datetime.date.today()}.csv",
                mime="text/csv",
                use_container_width=True
            )
        
        with col3:
            if st.button("🗑️ Clear Portfolio", use_container_width=True):
                st.session_state.portfolio = []
                st.success("✅ Portfolio cleared!")
                st.rerun()
    
    else:
        st.info("📝 Your portfolio is empty. Add some stocks to get started!")
    
    st.markdown('</div>', unsafe_allow_html=True)

# REPORTS PAGE
elif st.session_state.current_page == "reports":
    st.markdown('<div class="page-container">', unsafe_allow_html=True)
    st.title("📈 Portfolio Reports")
    
    if not st.session_state.portfolio:
        st.warning("⚠️ Your portfolio is empty. Add some stocks first!")
        if st.button("➕ Go to Portfolio", type="primary"):
            st.session_state.current_page = "portfolio"
            st.rerun()
    else:
        df = pd.DataFrame(st.session_state.portfolio)
        
        # Report overview
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📊 Portfolio Summary")
            
            # Risk analysis
            high_risk = len(df[df['rsi'] > 70])
            low_risk = len(df[df['rsi'] < 30])
            medium_risk = len(df) - high_risk - low_risk
            
            st.metric("🔴 High Risk", high_risk)
            st.metric("🟡 Medium Risk", medium_risk)
            st.metric("🟢 Low Risk", low_risk)
            
            # Portfolio score
            portfolio_score = (low_risk * 10 + medium_risk * 5 + high_risk * 2) / len(df) if len(df) > 0 else 0
            st.metric("🎯 Portfolio Score", f"{portfolio_score:.1f}/10")
        
        with col2:
            st.subheader("📈 Performance Analysis")
            
            # Create pie chart for recommendations
            fig, ax = plt.subplots(figsize=(8, 6))
            recommendation_counts = df['recommendation'].value_counts()
            colors = ['#10b981' if 'BUY' in x else '#ef4444' if 'SELL' in x else '#f59e0b' for x in recommendation_counts.index]
            ax.pie(recommendation_counts.values, labels=recommendation_counts.index, autopct='%1.1f%%', colors=colors)
            ax.set_title('Portfolio Recommendations')
            st.pyplot(fig)
        
        # Generate PDF Report
        st.subheader("📄 Generate Report")
        
        if st.button("🖨️ Generate PDF Report", type="primary", use_container_width=True):
            try:
                # Create PDF
                pdf = PDFReport()
                pdf.add_page()
                
                pdf.set_font('Arial', 'B', 16)
                pdf.cell(0, 10, f'Portfolio Analysis - {datetime.date.today()}', 0, 1, 'C')
                pdf.ln(10)
                
                pdf.set_font('Arial', '', 12)
                pdf.cell(0, 8, f'Total Stocks: {len(df)}', 0, 1)
                pdf.cell(0, 8, f'Average RSI: {df["rsi"].mean():.2f}', 0, 1)
                pdf.cell(0, 8, f'Portfolio Score: {portfolio_score:.1f}/10', 0, 1)
                pdf.ln(10)
                
                # Add stock details
                for _, stock in df.iterrows():
                    pdf.set_font('Arial', 'B', 12)
                    pdf.cell(0, 8, f"{stock['ticker']}: {stock['recommendation']}", 0, 1)
                    pdf.set_font('Arial', '', 10)
                    pdf.cell(0, 6, f"Price: ${stock['price']:.2f}, RSI: {stock['rsi']:.1f}", 0, 1)
                    pdf.ln(2)
                
                # Save PDF
                os.makedirs("reports", exist_ok=True)
                report_path = "reports/portfolio_report.pdf"
                pdf.output(report_path)
                
                # Download button
                with open(report_path, "rb") as file:
                    st.download_button(
                        "📥 Download PDF Report",
                        file.read(),
                        file_name=f"MarketPulse_Report_{datetime.date.today()}.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )
                
                st.success("✅ Report generated successfully!")
                
            except Exception as e:
                st.error(f"❌ Error generating report: {str(e)}")
    
    st.markdown('</div>', unsafe_allow_html=True)

# ABOUT PAGE
elif st.session_state.current_page == "about":
    st.markdown('<div class="page-container">', unsafe_allow_html=True)
    st.title("ℹ️ About MarketPulse")
    
    st.markdown("""
    ## 🚀 What is MarketPulse?
    
    MarketPulse is a smart stock analysis platform designed specifically for young investors. 
    We combine cutting-edge technology with simple, easy-to-understand insights.
    
    ## 🎯 Our Mission
    
    To make stock analysis accessible and fun for everyone, especially beginners in their 20s 
    who want to start their investment journey with confidence.
    
    ## 🔧 Features
    
    - **Smart Analysis**: AI-powered sentiment analysis from news and social media
    - **Technical Indicators**: RSI, Moving Averages, MACD, and more
    - **Seasonal Patterns**: Historical data to find the best trading times
    - **Portfolio Builder**: Create and manage your stock portfolio
    - **PDF Reports**: Generate comprehensive analysis reports
    
    ## 📊 How It Works
    
    1. **Analyze**: Enter any stock ticker to get instant analysis
    2. **Build**: Add stocks to your portfolio with one click  
    3. **Monitor**: Track your portfolio performance over time
    4. **Report**: Generate detailed reports to share or save
    
    ## 🌟 Why MarketPulse?
    
    - **Beginner-Friendly**: No confusing jargon or complicated charts
    - **Modern Design**: Clean, colorful interface designed for young adults
    - **Real-Time Data**: Always up-to-date stock prices and news
    - **Free to Use**: Core features available at no cost
    
    ---
    
    Made with ❤️ for the next generation of investors
    """)
    
    if st.button("🚀 Get Started", type="primary", use_container_width=True):
        st.session_state.current_page = "home"
        st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)
        
        # Email Report
        st.subheader("📧 Email Report")
        
        col1, col2 = st.columns(2)
        
        with col1:
            sender_email = st.text_input("📧 Your Gmail:", placeholder="your.email@gmail.com")
            recipient_email = st.text_input("📧 Send to:", placeholder="recipient@email.com")
        
        with col2:
            app_password = st.text_input("🔑 Gmail App Password:", type="password", help="Use Gmail App Password, not regular password")
        
        if st.button("📤 Send Email Report"):
            if sender_email and recipient_email and app_password:
                try:
                    report_path = "reports/marketpulse_comprehensive_report.pdf"
                    if os.path.exists(report_path):
                        send_email_report(sender_email, app_password, recipient_email, report_path)
                        st.success("✅ Report sent successfully!")
                    else:
                        st.error("❌ Please generate a report first")
                except Exception as e:
                    st.error(f"❌ Email failed: {str(e)}")
            else:
                st.warning("⚠️ Please fill in all email fields")