import smtplib
import sqlite3
from datetime import datetime
import time
import threading
from flask import Flask, request, render_template

app = Flask(__name__)

# Database setup
def init_db():
    conn = sqlite3.connect('emails.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS scheduled_emails (
            id INTEGER PRIMARY KEY,
            to_email TEXT,
            subject TEXT,
            message TEXT,
            send_time TEXT
        )
    ''')
    conn.commit()
    conn.close()

# Function to send an email
def send_email(sender_email, sender_password, to_email, subject, message):
    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            email_message = f"Subject: {subject}\n\n{message}"
            server.sendmail(sender_email, to_email, email_message)
            print(f"Email sent to {to_email}")
    except Exception as e:
        print(f"Failed to send email: {e}")

# Schedule email
def schedule_email(to_email, subject, message, send_time):
    conn = sqlite3.connect('emails.db')
    c = conn.cursor()
    c.execute('''
        INSERT INTO scheduled_emails (to_email, subject, message, send_time)
        VALUES (?, ?, ?, ?)
    ''', (to_email, subject, message, send_time))
    conn.commit()
    conn.close()

# Check and send emails at the scheduled time
def email_scheduler(sender_email, sender_password):
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
            send_email(sender_email, sender_password, email[1], email[2], email[3])
            c.execute('DELETE FROM scheduled_emails WHERE id = ?', (email[0],))
            conn.commit()
        conn.close()
        time.sleep(60)

# Start the email scheduler in a background thread
def start_scheduler(sender_email, sender_password):
    scheduler_thread = threading.Thread(target=email_scheduler, args=(sender_email, sender_password), daemon=True)
    scheduler_thread.start()

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        sender_email = request.form['sender_email']
        sender_password = request.form['sender_password']
        to_email = request.form['to_email']
        subject = request.form['subject']
        message = request.form['message']
        send_time = request.form['send_time']

        start_scheduler(sender_email, sender_password)
        schedule_email(to_email, subject, message, send_time)
        return "Email scheduled successfully!"
    return render_template('index.html')

if __name__ == "__main__":
    init_db()
    app.run(host='0.0.0.0', port=5000)
