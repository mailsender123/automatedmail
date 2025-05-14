from http.server import SimpleHTTPRequestHandler, HTTPServer
import urllib.parse
import sqlite3

def schedule_email(to_email, subject, message, send_time):
    conn = sqlite3.connect('emails.db')
    c = conn.cursor()
    c.execute('''
        INSERT INTO scheduled_emails (to_email, subject, message, send_time)
        VALUES (?, ?, ?, ?)
    ''', (to_email, subject, message, send_time))
    conn.commit()
    conn.close()

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

        to_email = data['to_email'][0]
        subject = data['subject'][0]
        message = data['message'][0]
        send_time = data['send_time'][0]

        schedule_email(to_email, subject, message, send_time)

        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(b'Email scheduled successfully!')

def run_server():
    server_address = ('0.0.0.0', 8080)
    httpd = HTTPServer(server_address, EmailSchedulerHandler)
    print("Web server running on port 8080...")
    httpd.serve_forever()

run_server()
