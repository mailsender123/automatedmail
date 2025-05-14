import sqlite3
from datetime import datetime
import time
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
import os

SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
SENDER_EMAIL = os.getenv("SENDER_EMAIL")

def send_email(to_email, subject, message):
    try:
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        email_message = Mail(
            from_email=SENDER_EMAIL,
            to_emails=to_email,
            subject=subject,
            plain_text_content=message
        )
        response = sg.send(email_message)
        print(f"Status Code: {response.status_code}")
    except Exception as e:
        print(f"Failed to send email: {e}")

def email_scheduler():
    while True:
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        conn = sqlite3.connect('emails.db')
        c = conn.cursor()
        c.execute('''
            SELECT id, to_email, subject, message FROM scheduled_emails 
            WHERE send_time <= ?
        ''', (now,))
        emails = c.fetchall()
        for email in emails:
            send_email(email[1], email[2], email[3])
            c.execute('DELETE FROM scheduled_emails WHERE id = ?', (email[0],))
            conn.commit()
        conn.close()
        time.sleep(60)

print("Starting scheduler...")
email_scheduler()
