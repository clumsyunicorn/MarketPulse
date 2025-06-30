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
    initial_sidebar_state="expanded",
    page_icon="📊"
)

# Custom CSS for hip design
st.markdown("""
<style>
    .main > div {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 15px;
        margin: 1rem 0;
    }
    
    .stMetric {
        background: rgba(255, 255, 255, 0.1);
        padding: 1rem;
        border-radius: 10px;
        backdrop-filter: blur(10px);
    }
    
    .stock-card {
        background: rgba(255, 255, 255, 0.1);
        padding: 1.5rem;
        border-radius: 15px;
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.2);
        margin: 1rem 0;
    }
    
    .floating-stocks {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        z-index: -1;
        pointer-events: none;
        overflow: hidden;
    }
    
    .stock-icon {
        position: absolute;
        font-size: 3rem;
        animation: float 6s ease-in-out infinite;
        opacity: 0.3;
    }
    
    @keyframes float {
        0%, 100% { transform: translateY(0px); }
        50% { transform: translateY(-20px); }
    }
    
    .hero-title {
        font-size: 3rem;
        font-weight: bold;
        background: linear-gradient(45deg, #FF6B6B, #4ECDC4, #45B7D1, #96CEB4);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 2rem;
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

def create_floating_animation():
    """Create floating stock icons animation"""
    stock_symbols = ['📈', '💹', '📊', '💰', '🏢', '📉', '💲', '🎯', '📋', '💸']
    
    animation_html = """
    <div class="floating-stocks">
    """
    
    for i, symbol in enumerate(stock_symbols):
        left = (i * 10) % 90
        delay = i * 0.5
        animation_html += f"""
        <div class="stock-icon" style="left: {left}%; animation-delay: {delay}s;">
            {symbol}
        </div>
        """
    
    animation_html += "</div>"
    return animation_html

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

# Sidebar Navigation
st.sidebar.markdown("## 📊 MarketPulse Navigation")
st.sidebar.markdown("*Smart Stock Advisor with AI*")
section = st.sidebar.radio(
    "Navigate to:",
    ["🏠 Home", "📈 Stock Analysis", "📁 Portfolio Builder", "📄 Reports & Analytics"],
    key="navigation"
)

# HOME SECTION
if section == "🏠 Home":
    # Floating animation background
    st.markdown(create_floating_animation(), unsafe_allow_html=True)
    
    st.markdown('<h1 class="hero-title">MarketPulse</h1>', unsafe_allow_html=True)
    st.markdown("### 🎯 *Your AI-Powered Stock Timing Advisor*")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="stock-card">
            <h3>📊 Smart Analysis</h3>
            <p>Advanced technical indicators combined with sentiment analysis from news and social media</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="stock-card">
            <h3>🎯 Perfect Timing</h3>
            <p>Seasonal patterns and historical data help identify optimal entry and exit points</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="stock-card">
            <h3>📈 Portfolio Power</h3>
            <p>Build, analyze, and export comprehensive portfolios with detailed reports</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown("### 🚀 Get Started")
    st.markdown("1. **Analyze** individual stocks with our comprehensive toolkit")
    st.markdown("2. **Build** your portfolio with data-driven selections")
    st.markdown("3. **Export** detailed reports and analysis")

# STOCK ANALYSIS SECTION
elif section == "📈 Stock Analysis":
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
elif section == "📁 Portfolio Builder":
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
elif section == "📄 Reports & Analytics":
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

# Footer
st.markdown("---")
st.markdown("### 🚀 MarketPulse - Powered by AI & Data Science")
st.markdown("*Making smart investment decisions through comprehensive analysis*")