import smtplib
from email.message import EmailMessage

def send_report_via_email(sender_email, app_password, recipient_email, attachment_path):
    msg = EmailMessage()
    msg["Subject"] = "Your MarketPulse Report"
    msg["From"] = sender_email
    msg["To"] = recipient_email
    msg.set_content("Attached is your MarketPulse stock analysis report.")

    with open(attachment_path, "rb") as f:
        file_data = f.read()
        msg.add_attachment(file_data, maintype="application", subtype="pdf", filename="MarketPulse_Report.pdf")

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(sender_email, app_password)
        smtp.send_message(msg)
