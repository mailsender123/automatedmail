import gradio as gr
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.date import DateTrigger
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
import pytz
import logging
import os

# Setup logging for debugging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")
logging.getLogger("apscheduler").setLevel(logging.DEBUG)

# Initialize persistent scheduler with SQLite job store
jobstores = {"default": SQLAlchemyJobStore(url="sqlite:///jobs.sqlite")}
scheduler = BackgroundScheduler(jobstores=jobstores)
scheduler.start()

# Email sender function
def send_email(sender_email, sender_password, recipient_email, subject, body):
    try:
        logging.info("Executing scheduled job to send email.")

        # Compose the email
        message = MIMEMultipart()
        message["From"] = sender_email
        message["To"] = recipient_email
        message["Subject"] = subject
        message.attach(MIMEText(body, "plain"))

        # Connect to the SMTP server
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.set_debuglevel(1)  # Enable SMTP debugging
            server.starttls()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, recipient_email, message.as_string())

        logging.info(f"Email sent successfully to {recipient_email}")
        return f"Email sent successfully to {recipient_email}"
    except smtplib.SMTPException as smtp_error:
        logging.error(f"SMTP error occurred: {smtp_error}")
        return f"SMTP error occurred: {smtp_error}"
    except Exception as e:
        logging.error(f"General error occurred: {e}")
        return f"General error occurred: {e}"

# Schedule email function
def schedule_email(sender_email, sender_password, recipient_email, subject, body, date, time_str, am_pm):
    try:
        # Parse date and time
        time_parts = [int(x) for x in time_str.split(":")]
        if am_pm.lower() == "pm" and time_parts[0] != 12:
            time_parts[0] += 12
        elif am_pm.lower() == "am" and time_parts[0] == 12:
            time_parts[0] = 0

        # Create a datetime object in the local timezone
        local_timezone = pytz.timezone("Asia/Kolkata")  # Update this to your timezone
        scheduled_datetime = datetime.strptime(date, "%Y-%m-%d").replace(
            hour=time_parts[0], minute=time_parts[1], second=0
        )
        scheduled_datetime = local_timezone.localize(scheduled_datetime)

        # Ensure the scheduled time is in the future
        if scheduled_datetime <= datetime.now(local_timezone):
            return "The scheduled time is in the past. Please set a future date and time."

        # Schedule the email
        scheduler.add_job(
            send_email,
            DateTrigger(run_date=scheduled_datetime),
            args=[sender_email, sender_password, recipient_email, subject, body],
            id=f"{sender_email}_{scheduled_datetime.timestamp()}"
        )

        logging.info(f"Email scheduled for {scheduled_datetime.strftime('%Y-%m-%d %I:%M %p')} (local time).")
        return f"Email scheduled for {scheduled_datetime.strftime('%Y-%m-%d %I:%M %p')} (local time)."
    except Exception as e:
        logging.error(f"Error scheduling email: {e}")
        return f"Failed to schedule email: {e}"

# Gradio interface
def email_interface(sender_email, sender_password, recipient_email, subject, body, date, time_str, am_pm):
    return schedule_email(sender_email, sender_password, recipient_email, subject, body, date, time_str, am_pm)

# Create Gradio app
with gr.Blocks() as email_app:
    gr.Markdown("# Scheduled Email Sender")
    gr.Markdown("Enter the details below to schedule an email for a specific date and time.")

    with gr.Row():
        sender_email = gr.Textbox(label="Sender Email", placeholder="Your email")
        sender_password = gr.Textbox(label="Sender Password", type="password", placeholder="Your email password")
    recipient_email = gr.Textbox(label="Recipient Email", placeholder="Recipient's email")
    subject = gr.Textbox(label="Subject", placeholder="Email subject")
    body = gr.Textbox(label="Body", placeholder="Email content", lines=4)
    date = gr.Textbox(label="Date (YYYY-MM-DD)", placeholder="Schedule date")
    time_str = gr.Textbox(label="Time (HH:MM)", placeholder="Schedule time")
    am_pm = gr.Radio(["AM", "PM"], label="AM/PM", value="AM")
    send_button = gr.Button("Schedule Email")
    output = gr.Textbox(label="Status")

    send_button.click(
        email_interface,
        inputs=[sender_email, sender_password, recipient_email, subject, body, date, time_str, am_pm],
        outputs=output,
    )

# Run Gradio app with a public link
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 7860))
    email_app.launch(share=True)
