from fpdf import FPDF
from datetime import datetime

class PDF(FPDF):
    def header(self):
        self.image("assets/MPLogo.jpg", x=75, y=10, w=60)
        self.set_y(35)
        self.set_font("Helvetica", "B", 14)
        self.cell(0, 10, "MarketPulse Stock Report", ln=True, align="C")
        self.set_font("Helvetica", "", 10)
        self.cell(0, 10, f"Generated on {datetime.today().strftime('%Y-%m-%d')}", ln=True, align="C")
        self.ln(5)

    def add_stock_section(self, ticker, sentiment_label, sentiment_score, timeframe, score, score_explanations):
        self.set_font("Helvetica", "B", 12)
        self.cell(0, 10, f"📊 {ticker} Summary", ln=True)
        self.set_font("Helvetica", "", 10)

        # Timeframe
        self.cell(0, 8, f"Timeframe: {timeframe}", ln=True)

        # Sentiment summary
        self.cell(0, 8, f"Sentiment: {sentiment_label} ({sentiment_score})", ln=True)

        # MarketPulse Score
        self.set_font("Helvetica", "B", 11)
        self.cell(0, 8, f"MarketPulse Score: {score}/3", ln=True)
        self.set_font("Helvetica", "", 10)

        for explanation in score_explanations:
            self.multi_cell(0, 6, f"- {explanation}")
        self.ln(3)

        # Charts (RSI + MA50)
        try:
            self.image(f"reports/{ticker}_ma.png", w=170)
            self.ln(3)
            self.image(f"reports/{ticker}_rsi.png", w=170)
            self.ln(5)
        except:
            self.multi_cell(0, 6, "⚠️ Chart export failed or missing.")
            self.ln(3)

    def add_text(self, text):
        self.set_font("Helvetica", "", 10)
        self.multi_cell(0, 6, text)
        self.ln(2)

    def save(self, path):
        self.output(path)
