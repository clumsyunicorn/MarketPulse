# utils/report_generator.py
from fpdf import FPDF
from datetime import datetime

class PDF(FPDF):
    def header(self):
        self.image("assets/MPLogo.jpg", x=75, y=10, w=60)  # Logo centered
        self.set_y(35)  # Position text below logo
        self.set_font("Helvetica", "B", 14)
        self.cell(0, 10, "MarketPulse Stock Report", ln=True, align="C")
        self.set_font("Helvetica", "", 10)
        self.cell(0, 10, f"Generated on {datetime.today().strftime('%Y-%m-%d')}", ln=True, align="C")
        self.ln(5)

    def add_stock_section(self, ticker, sentiment_label, sentiment_score):
        self.set_font("Helvetica", "B", 12)
        self.cell(0, 10, f"📊 {ticker} Summary", ln=True)
        self.set_font("Helvetica", "", 10)
        self.cell(0, 8, f"Sentiment: {sentiment_label} ({sentiment_score})", ln=True)
        self.ln(3)

    def add_text(self, text):
        self.set_font("Helvetica", "", 10)
        self.multi_cell(0, 6, text)
        self.ln(2)

    def save(self, path):
        self.output(path)
