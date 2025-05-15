import threading
from flask import Flask, request, render_template, redirect, url_for
from datetime import datetime
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

app = Flask(__name__)
scheduled_emails = []

# Function to send email using SMTP
def send_email(sender, password, recipient, subject, content):
    try:
        msg = MIMEMultipart()
        msg['From'] = sender
        msg['To'] = recipient
        msg['Subject'] = subject
        msg.attach(MIMEText(content, 'plain'))

        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(sender, password)
            server.send_message(msg)
            print(f"Email sent to {recipient}")
    except Exception as e:
        print(f"Error sending email: {e}")

# Function to handle scheduling emails
def schedule_email(sender, password, recipient, subject, content, schedule_time):
    scheduled_emails.append((sender, password, recipient, subject, content, schedule_time))
    print(f"Email scheduled for {schedule_time}")

# Background scheduler function
def run_scheduler():
    while True:
        now = datetime.now()
        for email in scheduled_emails[:]:
            sender, password, recipient, subject, content, schedule_time = email
            if now >= schedule_time:
                send_email(sender, password, recipient, subject, content)
                scheduled_emails.remove(email)
        time.sleep(60)

# Flask routes
@app.route('/')
def home():
    return render_template('home.html')

@app.route('/schedule', methods=['POST'])
def schedule():
    sender = request.form['sender']
    password = request.form['password']
    recipient = request.form['recipient']
    subject = request.form['subject']
    content = request.form['message']
    schedule_time = datetime.strptime(request.form['time'], "%Y-%m-%dT%H:%M")
    schedule_email(sender, password, recipient, subject, content, schedule_time)
    return redirect(url_for('success'))

@app.route('/success')
def success():
    return render_template('success.html')

if __name__ == "__main__":
    # Run the scheduler in a separate thread
    threading.Thread(target=run_scheduler, daemon=True).start()
    # Run the Flask server
    app.run(host='0.0.0.0', port=5000)
