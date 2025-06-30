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
    page_title="MarketPulse - Seasonal Stock Advisor", 
    layout="wide",
    initial_sidebar_state="collapsed",
    page_icon="📊"
)

# Custom CSS for hip homepage design with floating animations
st.markdown("""
<style>
    /* Global Styles */
    .stApp {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    
    /* Hide Streamlit default elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Floating Stock Ticker Animation */
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
        width: 80px;
        height: 80px;
        border-radius: 15px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: bold;
        font-size: 14px;
        color: white;
        text-shadow: 0 2px 4px rgba(0,0,0,0.3);
        box-shadow: 0 8px 32px rgba(0,0,0,0.1);
        backdrop-filter: blur(4px);
        border: 1px solid rgba(255,255,255,0.2);
    }
    
    /* Floating animations with waterfall effect */
    @keyframes float1 {
        0% { transform: translateY(100vh) rotate(0deg); opacity: 0; }
        10% { opacity: 0.8; }
        90% { opacity: 0.8; }
        100% { transform: translateY(-100px) rotate(360deg); opacity: 0; }
    }
    
    @keyframes float2 {
        0% { transform: translateY(100vh) rotate(0deg); opacity: 0; }
        15% { opacity: 0.7; }
        85% { opacity: 0.7; }
        100% { transform: translateY(-100px) rotate(-360deg); opacity: 0; }
    }
    
    @keyframes float3 {
        0% { transform: translateY(100vh) rotate(0deg); opacity: 0; }
        20% { opacity: 0.6; }
        80% { opacity: 0.6; }
        100% { transform: translateY(-100px) rotate(180deg); opacity: 0; }
    }
    
    @keyframes bobbing {
        0%, 100% { transform: translateY(0px); }
        50% { transform: translateY(-20px); }
    }
    
    .float-1 { animation: float1 15s linear infinite; }
    .float-2 { animation: float2 18s linear infinite; }
    .float-3 { animation: float3 20s linear infinite; }
    .bobbing { animation: bobbing 3s ease-in-out infinite; }
    
    /* Header Navigation */
    .nav-container {
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        z-index: 1000;
        background: rgba(255,255,255,0.1);
        backdrop-filter: blur(10px);
        padding: 1rem 2rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-bottom: 1px solid rgba(255,255,255,0.2);
    }
    
    .logo {
        font-size: 1.8rem;
        font-weight: bold;
        color: white;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    
    .nav-links {
        display: flex;
        gap: 2rem;
        color: white;
        font-weight: 500;
        font-size: 1.1rem;
    }
    
    .nav-link {
        cursor: pointer;
        transition: all 0.3s ease;
        padding: 0.5rem 1rem;
        border-radius: 25px;
    }
    
    .nav-link:hover {
        background: rgba(255,255,255,0.2);
        transform: translateY(-2px);
    }
    
    /* Hero Section */
    .hero-container {
        min-height: 100vh;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        text-align: center;
        padding: 2rem;
        margin-top: 80px;
    }
    
    .hero-title {
        font-size: 5rem;
        font-weight: 900;
        margin-bottom: 1rem;
        text-shadow: 0 4px 8px rgba(0,0,0,0.3);
        line-height: 1.1;
    }
    
    .stock-blue {
        background: linear-gradient(45deg, #4169E1, #1E90FF);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    
    .advisor-yellow {
        background: linear-gradient(45deg, #FFD700, #FFA500);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    
    .hero-subtitle {
        font-size: 1.4rem;
        color: white;
        margin-bottom: 3rem;
        max-width: 700px;
        line-height: 1.6;
        font-weight: 300;
    }
    
    /* Ticker Input Section */
    .ticker-input-container {
        background: rgba(255,255,255,0.15);
        backdrop-filter: blur(15px);
        border-radius: 25px;
        padding: 2.5rem;
        margin: 2rem 0;
        border: 1px solid rgba(255,255,255,0.2);
        box-shadow: 0 8px 32px rgba(0,0,0,0.1);
        max-width: 600px;
        width: 100%;
    }
    
    .ticker-input {
        width: 100%;
        padding: 1.2rem;
        border: none;
        border-radius: 15px;
        background: rgba(255,255,255,0.9);
        font-size: 1.1rem;
        margin-bottom: 1.5rem;
        box-shadow: inset 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .analyze-button {
        background: linear-gradient(45deg, #FFD700, #FFA500);
        color: #333;
        border: none;
        padding: 1.2rem 2.5rem;
        border-radius: 50px;
        font-size: 1.2rem;
        font-weight: bold;
        cursor: pointer;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(255,215,0,0.3);
        width: 100%;
    }
    
    .analyze-button:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 25px rgba(255,215,0,0.5);
    }
    
    /* Feature Cards */
    .features-container {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
        gap: 2rem;
        margin: 4rem 0;
        padding: 0 2rem;
        max-width: 1200px;
    }
    
    .feature-card {
        background: rgba(255,255,255,0.12);
        backdrop-filter: blur(15px);
        border-radius: 25px;
        padding: 2.5rem;
        text-align: center;
        border: 1px solid rgba(255,255,255,0.2);
        transition: all 0.4s ease;
        box-shadow: 0 8px 32px rgba(0,0,0,0.1);
    }
    
    .feature-card:hover {
        transform: translateY(-8px);
        box-shadow: 0 20px 40px rgba(0,0,0,0.2);
        background: rgba(255,255,255,0.18);
    }
    
    .feature-icon {
        font-size: 3.5rem;
        margin-bottom: 1.5rem;
        display: block;
    }
    
    .feature-title {
        font-size: 1.6rem;
        font-weight: bold;
        color: white;
        margin-bottom: 1rem;
    }
    
    .feature-description {
        color: rgba(255,255,255,0.85);
        line-height: 1.6;
        font-size: 1rem;
    }
    
    /* Action Buttons */
    .action-buttons {
        display: flex;
        gap: 1.5rem;
        justify-content: center;
        margin: 4rem 0;
        flex-wrap: wrap;
    }
    
    .action-btn {
        padding: 1.2rem 2.5rem;
        border-radius: 50px;
        border: none;
        font-weight: bold;
        cursor: pointer;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        font-size: 1.1rem;
        min-width: 180px;
    }
    
    .btn-orange {
        background: linear-gradient(45deg, #FF6B35, #F7931E);
        color: white;
    }
    
    .btn-blue {
        background: linear-gradient(45deg, #4A90E2, #357ABD);
        color: white;
    }
    
    .btn-yellow {
        background: linear-gradient(45deg, #FFD700, #FFA500);
        color: #333;
    }
    
    .action-btn:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 25px rgba(0,0,0,0.3);
    }
    
    /* Footer */
    .footer {
        text-align: center;
        padding: 3rem 2rem;
        color: rgba(255,255,255,0.7);
        font-size: 1rem;
        margin-top: 4rem;
        border-top: 1px solid rgba(255,255,255,0.1);
    }
    
    /* Responsive Design */
    @media (max-width: 768px) {
        .hero-title {
            font-size: 3rem;
        }
        
        .hero-subtitle {
            font-size: 1.2rem;
        }
        
        .nav-links {
            display: none;
        }
        
        .floating-ticker {
            width: 60px;
            height: 60px;
            font-size: 12px;
        }
        
        .features-container {
            grid-template-columns: 1fr;
            padding: 0 1rem;
        }
        
        .action-buttons {
            flex-direction: column;
            align-items: center;
        }
    }
    
    /* Streamlit specific overrides */
    .main .block-container {
        padding: 0 !important;
        max-width: none !important;
    }
    
    .stSelectbox, .stTextInput, .stButton {
        z-index: 1000;
    }
</style>
""", unsafe_allow_html=True)


def create_floating_tickers():
    """Generate floating stock ticker animations with waterfall effect"""
    tickers = [
        {"symbol": "TSLA", "color": "#DC2626", "left": 5, "delay": 0},
        {"symbol": "AMZN", "color": "#FF9500", "left": 15, "delay": 2},
        {"symbol": "GOOGL", "color": "#4285F4", "left": 25, "delay": 4},
        {"symbol": "MSFT", "color": "#00BCF2", "left": 35, "delay": 1},
        {"symbol": "NFLX", "color": "#E50914", "left": 45, "delay": 3},
        {"symbol": "COIN", "color": "#0052FF", "left": 55, "delay": 5},
        {"symbol": "SPY", "color": "#1DB954", "left": 65, "delay": 2.5},
        {"symbol": "DIS", "color": "#113CCF", "left": 75, "delay": 4.5},
        {"symbol": "AMD", "color": "#ED1C24", "left": 85, "delay": 1.5},
        {"symbol": "NVDA", "color": "#76B900", "left": 95, "delay": 3.5},
        {"symbol": "AAPL", "color": "#007AFF", "left": 10, "delay": 6},
        {"symbol": "META", "color": "#1877F2", "left": 20, "delay": 7},
        {"symbol": "UBER", "color": "#000000", "left": 30, "delay": 8},
        {"symbol": "SNAP", "color": "#FFFC00", "left": 40, "delay": 9},
        {"symbol": "TWTR", "color": "#1DA1F2", "left": 50, "delay": 10},
        {"symbol": "ZOOM", "color": "#2D8CFF", "left": 60, "delay": 11},
        {"symbol": "SHOP", "color": "#95BF47", "left": 70, "delay": 12},
        {"symbol": "SQ", "color": "#3E4348", "left": 80, "delay": 13},
        {"symbol": "PYPL", "color": "#009CDE", "left": 90, "delay": 14},
        {"symbol": "ROKU", "color": "#662D91", "left": 8, "delay": 15},
    ]
    
    floating_html = '<div class="floating-container">'
    
    # Create multiple layers for full coverage
    for layer in range(3):
        for i, ticker in enumerate(tickers):
            animation_class = f"float-{(i % 3) + 1}"
            left_offset = (layer * 2) % 8  # Slight horizontal offset per layer
            delay_offset = layer * 5  # Stagger layers
            
            floating_html += f'''
            <div class="floating-ticker {animation_class}" 
                 style="left: {(ticker['left'] + left_offset) % 100}%; 
                        background: {ticker['color']}; 
                        animation-delay: {ticker['delay'] + delay_offset}s;
                        opacity: {0.3 + (layer * 0.1)};">
                {ticker['symbol']}
            </div>
            '''
    
    floating_html += '</div>'
    return floating_html


def create_homepage():
    """Create the MarketPulse homepage with floating animations"""
    
    # Add floating tickers
    st.markdown(create_floating_tickers(), unsafe_allow_html=True)
    
    # Navigation
    nav_html = '''
    <div class="nav-container">
        <div class="logo">
            📊 MarketPulse
        </div>
        <div class="nav-links">
            <span class="nav-link">Dashboard</span>
            <span class="nav-link">Analysis</span>
            <span class="nav-link">Portfolio</span>
            <span class="nav-link">Reports</span>
        </div>
    </div>
    '''
    st.markdown(nav_html, unsafe_allow_html=True)
    
    # Hero Section
    hero_html = '''
    <div class="hero-container">
        <h1 class="hero-title">
            <span class="stock-blue">Seasonal Stock</span> <span class="advisor-yellow">Advisor</span>
        </h1>
        <p class="hero-subtitle">
            Harness the power of social sentiment analysis and comprehensive stock patterns 
            to build a perfect portfolio with optimal timing models.
        </p>
        
        <div class="ticker-input-container">
            <input type="text" class="ticker-input" placeholder="Enter stock tickers (e.g., AAPL, GOOGL, TSLA)" id="ticker-input">
            <button class="analyze-button" onclick="analyzeStocks()">Analyze Now</button>
        </div>
    </div>
    '''
    st.markdown(hero_html, unsafe_allow_html=True)
    
    # Feature Cards
    features_html = '''
    <div class="features-container">
        <div class="feature-card">
            <div class="feature-icon">📊</div>
            <div class="feature-title">Technical Analysis</div>
            <div class="feature-description">
                Advanced charting with RSI, moving averages, MACD, Bollinger Bands, and 20+ comprehensive technical indicators for precise market analysis.
            </div>
        </div>
        
        <div class="feature-card">
            <div class="feature-icon">🧠</div>
            <div class="feature-title">Sentiment Analysis</div>
            <div class="feature-description">
                Real-time social media and news sentiment tracking using AI-powered natural language processing to gauge market emotions.
            </div>
        </div>
        
        <div class="feature-card">
            <div class="feature-icon">⏰</div>
            <div class="feature-title">Timing Models</div>
            <div class="feature-description">
                Seasonal patterns and optimal entry/exit points based on historical data analysis and machine learning algorithms.
            </div>
        </div>
    </div>
    '''
    st.markdown(features_html, unsafe_allow_html=True)
    
    # Action Buttons
    action_buttons_html = '''
    <div class="action-buttons">
        <button class="action-btn btn-orange">Build Portfolio</button>
        <button class="action-btn btn-blue">Download Report</button>
        <button class="action-btn btn-yellow">Save Analysis</button>
    </div>
    '''
    st.markdown(action_buttons_html, unsafe_allow_html=True)
    
    # Footer
    footer_html = '''
    <div class="footer">
        <strong>Powered by advanced algorithms + real-time data + professional insights</strong>
    </div>
    '''
    st.markdown(footer_html, unsafe_allow_html=True)


# Utility Functions (keeping your existing functions)
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
        st.error(f"Error fetching Yahoo headlines: {e}")
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
    
    # Stochastic Oscillator
    low_14 = data['Low'].rolling(window=14).min()
    high_14 = data['High'].rolling(window=14).max()
    data['%K'] = 100 * ((data['Adj Close'] - low_14) / (high_14 - low_14))
    data['%D'] = data['%K'].rolling(window=3).mean()
    
    return data


class PDFReport(FPDF):
    def __init__(self):
        super().__init__()
        self.set_auto_page_break(auto=True, margin=15)
        
    def header(self):
        self.set_font('Arial', 'B', 15)
        self.cell(0, 10, 'MarketPulse - Comprehensive Portfolio Analysis Report', 0, 1, 'C')
        self.ln(10)
        
    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()} - Generated on {datetime.date.today()}', 0, 0, 'C')
        
    def add_stock_section(self, ticker, sentiment_label, sentiment_score, rsi, recommendation):
        self.ln(5)
        self.set_font('Arial', 'B', 14)
        self.cell(0, 10, f'Stock Analysis: {ticker}', 0, 1)
        
        self.set_font('Arial', '', 12)
        self.cell(0, 8, f'Sentiment: {sentiment_label} ({sentiment_score:.3f})', 0, 1)
        self.cell(0, 8, f'RSI: {rsi:.2f}', 0, 1)
        self.cell(0, 8, f'Recommendation: {recommendation}', 0, 1)
        self.ln(5)


def send_email_report(sender_email, app_password, recipient_email, report_path):
    """Send report via email"""
    try:
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = recipient_email
        msg['Subject'] = "MarketPulse - Your Portfolio Analysis Report"
        
        body = """
        Hello,
        
        Please find attached your comprehensive MarketPulse portfolio analysis report.
        
        This report includes:
        • Technical analysis with multiple indicators
        • Sentiment analysis from news sources
        • Seasonal trading patterns
        • Buy/sell recommendations
        • Risk assessment
        
        Best regards,
        MarketPulse Team
        """
        
        msg.attach(MIMEText(body, 'plain'))
        
        if os.path.exists(report_path):
            with open(report_path, "rb") as attachment:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(attachment.read())
                
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', f'attachment; filename= {os.path.basename(report_path)}')
            msg.attach(part)
        
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, app_password)
        server.sendmail(sender_email, recipient_email, msg.as_string())
        server.quit()
        return True
        
    except Exception as e:
        raise Exception(f"Email failed: {str(e)}")


# Initialize session state
if "portfolio" not in st.session_state:
    st.session_state.portfolio = []
if "current_page" not in st.session_state:
    st.session_state.current_page = "home"

# Check if we're on the homepage
if st.session_state.current_page == "home":
    create_homepage()
    
    # Add JavaScript for button functionality
    st.markdown("""
    <script>
    function analyzeStocks() {
        // This would integrate with Streamlit's session state
        alert('Analysis functionality would be implemented here!');
    }
    </script>
    """, unsafe_allow_html=True)

# Navigation logic (simplified for demo)
col1, col2, col3, col4 = st.columns(4)

with col1:
    if st.button("🏠 Home", key="nav_home"):
        st.session_state.current_page = "home"
        st.experimental_rerun()

with col2:
    if st.button("📈 Analysis", key="nav_analysis"):
        st.session_state.current_page = "analysis"
        st.experimental_rerun()

with col3:
    if st.button("📁 Portfolio", key="nav_portfolio"):
        st.session_state.current_page = "portfolio"
        st.experimental_rerun()

with col4:
    if st.button("📄 Reports", key="nav_reports"):
        st.session_state.current_page = "reports"
        st.experimental_rerun()

# STOCK ANALYSIS SECTION
if st.session_state.current_page == "analysis":
    st.title("📈 Comprehensive Stock Analysis")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        ticker = st.text_input("🔍 Enter Stock Ticker:", value="AAPL", help="Enter any valid stock symbol").upper()
    
    with col2:
        analysis_type = st.selectbox("Analysis Type:", ["Full Analysis", "Quick Check", "Technical Only"])
    
    col3, col4 = st.columns(2)
    with col3:
        start_date = st.date_input("📅 Start Date", datetime.date.today() - datetime.timedelta(days=365 * 2))
    with col4:
        end_date = st.date_input("📅 End Date", datetime.date.today())
    
    if st.button("🚀 Run Analysis", type="primary"):
        with st.spinner("🔄 Analyzing stock data..."):
            try:
                # Fetch stock data
                data = yf.download(ticker, start=start_date, end=end_date)
                
                if data.empty:
                    st.error("❌ No data found for this ticker")
                else:
                    # Calculate technical indicators
                    data = calculate_technical_indicators(data)
                    data['Return'] = data['Adj Close'].pct_change()
                    data['Month'] = data.index.month_name()
                    
                    # Current metrics
                    current_price = data['Adj Close'].iloc[-1]
                    current_rsi = data['RSI'].iloc[-1] if not pd.isna(data['RSI'].iloc[-1]) else 50
                    
                    # Display current metrics
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric("💰 Current Price", f"${current_price:.2f}", 
                                 f"{data['Return'].iloc[-1]*100:.2f}%")
                    
                    with col2:
                        rsi_color = "🟢" if current_rsi < 30 else "🔴" if current_rsi > 70 else "🟡"
                        st.metric(f"{rsi_color} RSI", f"{current_rsi:.1f}")
                    
                    with col3:
                        volume = data['Volume'].iloc[-1] if 'Volume' in data.columns else 0
                        st.metric("📊 Volume", f"{volume:,.0f}")
                    
                    with col4:
                        # Generate recommendation
                        recommendation = "BUY 🟢" if current_rsi < 30 else "SELL 🔴" if current_rsi > 70 else "HOLD 🟡"
                        st.metric("🎯 Signal", recommendation)
                    
                    # Seasonal Analysis
                    st.subheader("📅 Seasonal Performance Analysis")
                    monthly_returns = data.groupby('Month')['Return'].mean().reindex([
                        'January', 'February', 'March', 'April', 'May', 'June',
                        'July', 'August', 'September', 'October', 'November', 'December'
                    ]) * 100
                    
                    st.bar_chart(monthly_returns)
                    
                    # Best and worst months
                    best_month = monthly_returns.idxmax()
                    worst_month = monthly_returns.idxmin()
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.success(f"🟢 Best Month: **{best_month}** ({monthly_returns[best_month]:.2f}%)")
                    with col2:
                        st.error(f"🔴 Worst Month: **{worst_month}** ({monthly_returns[worst_month]:.2f}%)")
                    
                    # Technical Analysis Charts
                    st.subheader("📊 Technical Analysis")
                    
                    tab1, tab2, tab3 = st.tabs(["Price & Moving Averages", "RSI & Stochastic", "MACD & Bollinger Bands"])
                    
                    with tab1:
                        chart_data = data[['Adj Close', 'SMA_20', 'SMA_50', 'SMA_200']].dropna()
                        st.line_chart(chart_data)
                    
                    with tab2:
                        chart_data = data[['RSI', '%K', '%D']].dropna()
                        st.line_chart(chart_data)
                    
                    with tab3:
                        col1, col2 = st.columns(2)
                        with col1:
                            st.line_chart(data[['MACD', 'MACD_Signal']].dropna())
                        with col2:
                            st.line_chart(data[['Adj Close', 'BB_Upper', 'BB_Middle', 'BB_Lower']].dropna())
                    
                    # Sentiment Analysis
                    if analysis_type in ["Full Analysis", "Quick Check"]:
                        st.subheader("🧠 Market Sentiment Analysis")
                        
                        headlines = get_yahoo_finance_headlines(ticker)
                        if headlines:
                            results = analyze_sentiment(headlines)
                            avg_sentiment, sentiment_label = summarize_sentiment(results)
                            
                            col1, col2, col3 = st.columns(3)
                            
                            with col1:
                                sentiment_color = "🟢" if sentiment_label == "Positive" else "🔴" if sentiment_label == "Negative" else "🟡"
                                st.metric(f"{sentiment_color} Overall Sentiment", sentiment_label)
                            
                            with col2:
                                st.metric("📊 Sentiment Score", f"{avg_sentiment:.3f}")
                            
                            with col3:
                                st.metric("📰 News Articles", len(headlines))
                            
                            # Display headlines
                            with st.expander("📰 Recent Headlines"):
                                for result in results[:5]:
                                    emoji = "🟢" if result["label"] == "Positive" else "🔴" if result["label"] == "Negative" else "🟡"
                                    st.write(f"{emoji} **{result['headline']}** (Score: {result['score']:.3f})")
                        else:
                            st.warning("⚠️ No recent news headlines found")
                    
                    # Export options
                    st.subheader("💾 Export Data")
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        csv_data = data.to_csv().encode('utf-8')
                        st.download_button(
                            "📥 Download CSV Data",
                            csv_data,
                            file_name=f"{ticker}_analysis_{datetime.date.today()}.csv",
                            mime="text/csv"
                        )
                    
                    with col2:
                        if st.button("➕ Add to Portfolio"):
                            stock_data = {
                                "ticker": ticker,
                                "price": current_price,
                                "rsi": current_rsi,
                                "recommendation": recommendation,
                                "sentiment": sentiment_label if 'sentiment_label' in locals() else "N/A",
                                "added_date": str(datetime.date.today())
                            }
                            st.session_state.portfolio.append(stock_data)
                            st.success(f"✅ {ticker} added to portfolio!")
                            
            except Exception as e:
                st.error(f"❌ Analysis failed: {str(e)}")

# PORTFOLIO SECTION
elif st.session_state.current_page == "portfolio":
    st.title("📁 Smart Portfolio Builder")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("➕ Add Stocks to Portfolio")
        new_ticker = st.text_input("Stock Ticker:", placeholder="e.g., AAPL, GOOGL, TSLA").upper()
    
    with col2:
        st.subheader("⚙️ Portfolio Settings")
        auto_analysis = st.checkbox("Auto-analyze on add", value=True)
    
    if st.button("➕ Add Stock") and new_ticker:
        try:
            # Quick analysis for portfolio
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
            else:
                st.error("❌ Invalid ticker symbol")
        except Exception as e:
            st.error(f"❌ Error adding stock: {str(e)}")
    
    # Display Portfolio
    st.subheader("📊 Current Portfolio")
    
    if st.session_state.portfolio:
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
            if st.button("💾 Save Portfolio"):
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
                mime="text/csv"
            )
        
        with col3:
            if st.button("🗑️ Clear Portfolio"):
                st.session_state.portfolio = []
                st.success("✅ Portfolio cleared!")
                st.experimental_rerun()
        
        # Load saved portfolio
        if os.path.exists("reports/portfolio.json"):
            if st.button("📤 Load Saved Portfolio"):
                with open("reports/portfolio.json", "r") as f:
                    st.session_state.portfolio = json.load(f)
                st.success("✅ Portfolio loaded!")
                st.experimental_rerun()
    
    else:
        st.info("📝 Your portfolio is empty. Add some stocks to get started!")

# REPORTS SECTION
elif st.session_state.current_page == "reports":
    st.title("📄 Comprehensive Reports & Analytics")
    
    if not st.session_state.portfolio:
        st.warning("⚠️ Your portfolio is empty. Please add stocks first.")
    else:
        # Report generation
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📊 Portfolio Analytics")
            df = pd.DataFrame(st.session_state.portfolio)
            
            # Performance breakdown
            fig, ax = plt.subplots(figsize=(10, 6))
            recommendation_counts = df['recommendation'].value_counts()
            colors = ['green' if 'BUY' in x else 'red' if 'SELL' in x else 'orange' for x in recommendation_counts.index]
            ax.pie(recommendation_counts.values, labels=recommendation_counts.index, autopct='%1.1f%%', colors=colors)
            ax.set_title('Portfolio Recommendations Distribution')
            st.pyplot(fig)
            
            # RSI Distribution
            fig2, ax2 = plt.subplots(figsize=(10, 4))
            ax2.hist(df['rsi'], bins=20, alpha=0.7, color='skyblue', edgecolor='black')
            ax2.axvline(30, color='green', linestyle='--', label='Oversold (30)')
            ax2.axvline(70, color='red', linestyle='--', label='Overbought (70)')
            ax2.set_xlabel('RSI Values')
            ax2.set_ylabel('Frequency')
            ax2.set_title('Portfolio RSI Distribution')
            ax2.legend()
            st.pyplot(fig2)
        
        with col2:
            st.subheader("📈 Risk Assessment")
            
            # Risk metrics
            high_risk = len(df[df['rsi'] > 70])
            low_risk = len(df[df['rsi'] < 30])
            medium_risk = len(df) - high_risk - low_risk
            
            st.metric("🔴 High Risk (RSI > 70)", high_risk)
            st.metric("🟡 Medium Risk", medium_risk)
            st.metric("🟢 Low Risk (RSI < 30)", low_risk)
            
            # Portfolio score
            portfolio_score = (low_risk * 10 + medium_risk * 5 + high_risk * 2) / len(df) if len(df) > 0 else 0
            st.metric("🎯 Portfolio Score", f"{portfolio_score:.1f}/10")
        
        # Generate PDF Report
        st.subheader("📄 Generate PDF Report")
        
        if st.button("🖨️ Generate Comprehensive Report"):
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
                
                # Add individual stock analysis
                for _, stock in df.iterrows():
                    sentiment = stock.get('sentiment', 'N/A')
                    pdf.add_stock_section(
                        stock['ticker'], 
                        sentiment, 
                        0.0,  # Placeholder for sentiment score
                        stock['rsi'], 
                        stock['recommendation']
                    )
                
                # Save PDF
                os.makedirs("reports", exist_ok=True)
                report_path = "reports/marketpulse_comprehensive_report.pdf"
                pdf.output(report_path)
                
                # Download button
                with open(report_path, "rb") as file:
                    st.download_button(
                        "📥 Download PDF Report",
                        file.read(),
                        file_name=f"MarketPulse_Report_{datetime.date.today()}.pdf",
                        mime="application/pdf"
                    )
                
                st.success("✅ Report generated successfully!")
                
            except Exception as e:
                st.error(f"❌ Report generation failed: {str(e)}")
        
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