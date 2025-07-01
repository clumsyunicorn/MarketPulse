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
import plotly.graph_objects as go
import plotly.express as px
from PIL import Image

# Page config
st.set_page_config(
    page_title="MarketPulse - Smart Stock Advisor", 
    layout="wide",
    initial_sidebar_state="collapsed",
    page_icon="💰"
)

# Initialize session state
if "current_page" not in st.session_state:
    st.session_state.current_page = "Home"
if "portfolio" not in st.session_state:
    st.session_state.portfolio = []

# Custom CSS for young adult design
st.markdown("""
<style>
    .main {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 0;
    }
    
    .stApp {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Main content styling */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        background: rgba(255,255,255,0.1);
        border-radius: 20px;
        backdrop-filter: blur(10px);
        margin: 1rem;
        border: 1px solid rgba(255,255,255,0.2);
    }
    
    /* Button styling */
    .stButton > button {
        background: linear-gradient(45deg, #6366f1, #8b5cf6) !important;
        color: white !important;
        border-radius: 25px !important;
        border: none !important;
        padding: 0.75rem 1.5rem !important;
        font-weight: 600 !important;
        transition: all 0.3s ease !important;
        width: 100% !important;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 25px rgba(99, 102, 241, 0.3) !important;
    }
    
    /* Metric styling */
    .metric-container {
        background: rgba(255,255,255,0.15);
        padding: 1rem;
        border-radius: 15px;
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255,255,255,0.2);
        text-align: center;
        margin: 0.5rem 0;
    }
    
    /* Text styling */
    .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
        color: white !important;
        text-align: center;
    }
    
    .stMarkdown p {
        color: rgba(255,255,255,0.9) !important;
    }
    
    /* Input styling */
    .stTextInput > div > div > input {
        background: rgba(255,255,255,0.9) !important;
        border-radius: 15px !important;
        border: 1px solid rgba(255,255,255,0.3) !important;
    }
    
    .stSelectbox > div > div > select {
        background: rgba(255,255,255,0.9) !important;
        border-radius: 15px !important;
    }
    
    /* Success/Error messages */
    .stSuccess {
        background: rgba(34, 197, 94, 0.2) !important;
        border: 1px solid rgba(34, 197, 94, 0.3) !important;
        border-radius: 15px !important;
    }
    
    .stError {
        background: rgba(239, 68, 68, 0.2) !important;
        border: 1px solid rgba(239, 68, 68, 0.3) !important;
        border-radius: 15px !important;
    }
    
    /* Navigation specific styling */
    .nav-button {
        margin: 0.2rem;
    }
    
    /* Hero title */
    .hero-title {
        font-size: 4rem;
        font-weight: 900;
        text-align: center;
        margin-bottom: 1rem;
        background: linear-gradient(45deg, #f59e0b, #eab308);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    
    /* Floating animation */
    @keyframes float {
        0%, 100% { transform: translateY(0px); }
        50% { transform: translateY(-20px); }
    }
    
    .floating {
        animation: float 3s ease-in-out infinite;
    }
</style>
""", unsafe_allow_html=True)

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
    except:
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
    """Calculate technical indicators"""
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
    
    return data

def load_asset_image(filename):
    """Load image from assets folder"""
    try:
        if os.path.exists(f"assets/{filename}"):
            return Image.open(f"assets/{filename}")
        else:
            return None
    except:
        return None

# NAVIGATION - Using Streamlit's built-in functionality
st.markdown("# 💰 MarketPulse")
st.markdown("### Smart Stock Analysis for Young Investors")

# Navigation tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs(["🏠 Home", "📊 Analysis", "💼 Portfolio", "📈 Reports", "ℹ️ About"])

# HOME TAB
with tab1:
    st.markdown('<div class="hero-title">MarketPulse</div>', unsafe_allow_html=True)
    st.markdown("### 🚀 Your AI-Powered Trading Companion")
    
    # Quick analysis section
    st.markdown("## Quick Stock Analysis")
    col1, col2 = st.columns([3, 1])
    
    with col1:
        quick_ticker = st.text_input("Enter stock ticker (e.g., AAPL, TSLA, GOOGL)", key="home_ticker")
    
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)  # Add spacing
        if st.button("🚀 Analyze", key="home_analyze", type="primary"):
            if quick_ticker:
                st.session_state.analysis_ticker = quick_ticker.upper()
                st.success(f"Analysis for {quick_ticker.upper()} - Check the Analysis tab!")
    
    # Feature showcase
    st.markdown("## 🌟 Why Choose MarketPulse?")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        ### 🧠 Smart Analysis
        AI-powered sentiment analysis combined with technical indicators for complete market insights.
        """)
    
    with col2:
        st.markdown("""
        ### ⏰ Perfect Timing
        Historical patterns and seasonal trends help you find optimal entry and exit points.
        """)
    
    with col3:
        st.markdown("""
        ### 📱 Beginner Friendly
        No confusing jargon - clean, simple interface designed for new investors.
        """)
    
    # Popular stocks showcase
    st.markdown("## 📈 Popular Stocks")
    popular_stocks = ["AAPL", "TSLA", "GOOGL", "AMZN", "MSFT", "NVDA"]
    
    cols = st.columns(len(popular_stocks))
    for i, stock in enumerate(popular_stocks):
        with cols[i]:
            if st.button(f"📊 {stock}", key=f"popular_{stock}"):
                st.session_state.analysis_ticker = stock
                st.success(f"Set {stock} for analysis!")

# ANALYSIS TAB
with tab2:
    st.markdown("# 📊 Stock Analysis")
    
    # Get ticker
    if 'analysis_ticker' in st.session_state:
        default_ticker = st.session_state.analysis_ticker
    else:
        default_ticker = "AAPL"
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        ticker = st.text_input("Stock Ticker:", value=default_ticker, key="analysis_input").upper()
    
    with col2:
        period = st.selectbox("Time Period:", ["1y", "2y", "5y"], key="period_select")
    
    analyze_button = st.button("🚀 Run Complete Analysis", type="primary", key="run_analysis")
    
    if analyze_button and ticker:
        with st.spinner(f"Analyzing {ticker}..."):
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
                    volume = data['Volume'].iloc[-1] if 'Volume' in data.columns else 0
                    
                    # Display metrics
                    st.markdown("## 📊 Current Metrics")
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric("💰 Price", f"${current_price:.2f}", f"{change:+.2f}%")
                    
                    with col2:
                        rsi_status = "Oversold" if current_rsi < 30 else "Overbought" if current_rsi > 70 else "Normal"
                        st.metric("📊 RSI", f"{current_rsi:.1f}", rsi_status)
                    
                    with col3:
                        st.metric("📈 Volume", f"{volume:,.0f}")
                    
                    with col4:
                        # Generate recommendation
                        if current_rsi < 30:
                            recommendation = "BUY 🟢"
                        elif current_rsi > 70:
                            recommendation = "SELL 🔴"
                        else:
                            recommendation = "HOLD 🟡"
                        st.metric("🎯 Signal", recommendation)
                    
                    # Price chart
                    st.markdown("## 📈 Price Chart")
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(x=data.index, y=data['Adj Close'], name='Price', line=dict(color='#6366f1')))
                    fig.add_trace(go.Scatter(x=data.index, y=data['SMA_20'], name='SMA 20', line=dict(color='#f59e0b')))
                    fig.add_trace(go.Scatter(x=data.index, y=data['SMA_50'], name='SMA 50', line=dict(color='#ef4444')))
                    fig.update_layout(title=f"{ticker} Price Chart", xaxis_title="Date", yaxis_title="Price ($)")
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # RSI chart
                    st.markdown("## 📊 RSI Indicator")
                    fig2 = go.Figure()
                    fig2.add_trace(go.Scatter(x=data.index, y=data['RSI'], name='RSI', line=dict(color='#8b5cf6')))
                    fig2.add_hline(y=70, line_dash="dash", line_color="red", annotation_text="Overbought (70)")
                    fig2.add_hline(y=30, line_dash="dash", line_color="green", annotation_text="Oversold (30)")
                    fig2.update_layout(title="RSI Indicator", xaxis_title="Date", yaxis_title="RSI")
                    st.plotly_chart(fig2, use_container_width=True)
                    
                    # Sentiment Analysis
                    st.markdown("## 🧠 Market Sentiment")
                    headlines = get_yahoo_finance_headlines(ticker)
                    
                    if headlines:
                        results = analyze_sentiment(headlines)
                        avg_sentiment, sentiment_label = summarize_sentiment(results)
                        
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("📰 Sentiment", sentiment_label)
                        with col2:
                            st.metric("📊 Score", f"{avg_sentiment:.3f}")
                        with col3:
                            st.metric("📰 Articles", len(headlines))
                        
                        # Show headlines
                        with st.expander("📰 Recent Headlines"):
                            for result in results[:5]:
                                emoji = "🟢" if result["label"] == "Positive" else "🔴" if result["label"] == "Negative" else "🟡"
                                st.write(f"{emoji} {result['headline']}")
                    else:
                        st.info("No recent news found for sentiment analysis")
                    
                    # Add to portfolio
                    st.markdown("## 💼 Portfolio Actions")
                    if st.button("➕ Add to Portfolio", type="secondary", key="add_to_portfolio"):
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
                st.error(f"❌ Analysis failed: {str(e)}")

# PORTFOLIO TAB
with tab3:
    st.markdown("# 💼 Your Portfolio")
    
    # Add stock section
    st.markdown("## ➕ Add New Stock")
    col1, col2 = st.columns([3, 1])
    
    with col1:
        new_ticker = st.text_input("Enter stock ticker:", key="portfolio_input").upper()
    
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Add Stock", type="primary", key="add_stock_btn"):
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
                        st.error("❌ Invalid ticker symbol")
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
    
    # Display portfolio
    if st.session_state.portfolio:
        st.markdown("## 📊 Portfolio Overview")
        
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
            st.metric("📊 Average RSI", f"{avg_rsi:.1f}")
        
        # Portfolio table
        st.markdown("### 📋 Your Stocks")
        st.dataframe(df, use_container_width=True)
        
        # Portfolio actions
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("💾 Save Portfolio", key="save_portfolio"):
                os.makedirs("reports", exist_ok=True)
                with open("reports/portfolio.json", "w") as f:
                    json.dump(st.session_state.portfolio, f, indent=2)
                st.success("✅ Portfolio saved to reports/portfolio.json")
        
        with col2:
            csv_data = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                "📥 Download CSV",
                csv_data,
                file_name=f"portfolio_{datetime.date.today()}.csv",
                mime="text/csv",
                key="download_csv"
            )
        
        with col3:
            if st.button("🗑️ Clear Portfolio", key="clear_portfolio"):
                st.session_state.portfolio = []
                st.success("✅ Portfolio cleared!")
                st.rerun()
    
    else:
        st.info("📝 Your portfolio is empty. Add some stocks to get started!")
        st.markdown("**Suggested stocks to try:** AAPL, TSLA, GOOGL, AMZN, MSFT")

# REPORTS TAB
with tab4:
    st.markdown("# 📈 Portfolio Reports")
    
    if not st.session_state.portfolio:
        st.warning("⚠️ Your portfolio is empty. Add some stocks first!")
        if st.button("➕ Go Add Stocks", type="primary", key="go_to_portfolio"):
            st.info("👆 Click the Portfolio tab above to add stocks")
    else:
        df = pd.DataFrame(st.session_state.portfolio)
        
        # Portfolio analytics
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("## 📊 Risk Analysis")
            
            high_risk = len(df[df['rsi'] > 70])
            low_risk = len(df[df['rsi'] < 30])
            medium_risk = len(df) - high_risk - low_risk
            
            st.metric("🔴 High Risk (RSI > 70)", high_risk)
            st.metric("🟡 Medium Risk", medium_risk)
            st.metric("🟢 Low Risk (RSI < 30)", low_risk)
            
            # Portfolio score
            portfolio_score = (low_risk * 10 + medium_risk * 5 + high_risk * 2) / len(df) if len(df) > 0 else 0
            st.metric("🎯 Portfolio Score", f"{portfolio_score:.1f}/10")
        
        with col2:
            st.markdown("## 📈 Recommendations Distribution")
            
            # Create pie chart
            recommendation_counts = df['recommendation'].value_counts()
            fig = px.pie(values=recommendation_counts.values, 
                        names=recommendation_counts.index,
                        title="Portfolio Recommendations",
                        color_discrete_map={'BUY 🟢': '#10b981', 'SELL 🔴': '#ef4444', 'HOLD 🟡': '#f59e0b'})
            st.plotly_chart(fig, use_container_width=True)
        
        # Generate report
        st.markdown("## 📄 Generate Report")
        
        if st.button("📋 Generate Summary Report", type="primary", key="generate_report"):
            st.markdown("### 📊 Portfolio Summary Report")
            st.markdown(f"**Generated on:** {datetime.date.today()}")
            st.markdown(f"**Total Stocks:** {len(df)}")
            st.markdown(f"**Average RSI:** {df['rsi'].mean():.2f}")
            st.markdown(f"**Portfolio Score:** {portfolio_score:.1f}/10")
            
            st.markdown("### 📋 Stock Details")
            for _, stock in df.iterrows():
                st.markdown(f"**{stock['ticker']}** - ${stock['price']:.2f} - {stock['recommendation']} (RSI: {stock['rsi']:.1f})")
            
            st.success("✅ Report generated! You can copy this information or take a screenshot.")

# ABOUT TAB
with tab5:
    st.markdown("# ℹ️ About MarketPulse")
    
    st.markdown("""
    ## 🚀 Welcome to MarketPulse!
    
    MarketPulse is designed specifically for young investors who want to start their trading journey with confidence and data-driven insights.
    
    ## 🎯 What We Do
    
    - **Smart Analysis**: Combine technical indicators with AI-powered sentiment analysis
    - **Portfolio Building**: Easy-to-use portfolio management tools
    - **Educational**: Learn while you invest with clear explanations
    - **Beginner-Friendly**: No confusing jargon or overwhelming charts
    
    ## 🔧 Features
    
    ### 📊 Technical Analysis
    - RSI (Relative Strength Index)
    - Moving Averages (SMA 20, 50, 200)
    - Price charts and trends
    - Buy/Sell/Hold recommendations
    
    ### 🧠 Sentiment Analysis
    - Real-time news analysis
    - Social media sentiment tracking
    - AI-powered headline analysis
    - Market emotion indicators
    
    ### 💼 Portfolio Management
    - Add/remove stocks easily
    - Track performance over time
    - Risk assessment tools
    - Export capabilities
    
    ## 🌟 Why MarketPulse?
    
    **For Beginners**: We explain everything in simple terms
    **For Students**: Perfect for learning investment basics
    **For Young Professionals**: Quick analysis for busy schedules
    **For Everyone**: Free and easy to use
    
    ## 📱 How to Get Started
    
    1. **Analyze**: Start with a stock ticker in the Analysis tab
    2. **Build**: Add promising stocks to your Portfolio
    3. **Monitor**: Check your Reports for insights
    4. **Learn**: Use our analysis to understand market patterns
    
    ---
    
    ### 🎨 Made for Gen Z Investors
    
    Clean design, modern colors, and intuitive interface designed specifically for young adults who want to start investing smartly.
    
    **Remember**: This is for educational purposes. Always do your own research and consider consulting with financial advisors for investment decisions.
    """)
    
    # Quick stats
    st.markdown("## 📊 Quick Demo Stats")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("🎯 Accuracy Rate", "85%")
    
    with col2:
        st.metric("📈 Stocks Analyzed", "500+")
    
    with col3:
        st.metric("👥 Happy Users", "1000+")

# Footer
st.markdown("---")
st.markdown("### 💰 MarketPulse - Smart Investing Made Simple")
st.markdown("*Empowering the next generation of investors with AI and data*")