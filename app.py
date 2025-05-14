import smtplib
import sqlite3
from datetime import datetime
import time
import threading
from http.server import SimpleHTTPRequestHandler, HTTPServer
import urllib.parse

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

# Custom HTTP Request Handler
class EmailSchedulerHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            with open('templates/index.html', 'rb') as file:
                self.wfile.write(file.read())
        else:
            super().do_GET()

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length).decode()
        data = urllib.parse.parse_qs(post_data)

        sender_email = data['sender_email'][0]
        sender_password = data['sender_password'][0]
        to_email = data['to_email'][0]
        subject = data['subject'][0]
        message = data['message'][0]
        send_time = data['send_time'][0]

        start_scheduler(sender_email, sender_password)
        schedule_email(to_email, subject, message, send_time)

        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(b'Email scheduled successfully!')

# Start HTTP server
def run_server():
    server_address = ('0.0.0.0', 8080)
    httpd = HTTPServer(server_address, EmailSchedulerHandler)
    print("Server running on port 8080...")
    httpd.serve_forever()

# Initialize the database
init_db()
run_server()
