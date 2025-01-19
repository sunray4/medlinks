import smtplib
from email.mime.text import MIMEText

def send_email_to_doctor(sender_email, sender_password, doctor_email, doctor_name, patient_name, appointment_time):
  
    subject = "Appointment Scheduled with Patient"
    body = f"""
    <html>
        <body>
            <p>Dear Dr. {doctor_name},</p>
            <p>An appointment has been scheduled with your patient, <b>{patient_name}</b>, for the following time:</p>
            <p><b>Appointment Time:</b> {appointment_time}</p>
            <p>Best regards,<br>Your Appointment Team</p>
        </body>
    </html>
    """
    
    # Create the MIMEText email message with HTML content
    html_message = MIMEText(body, 'html')
    html_message['Subject'] = subject
    html_message['From'] = sender_email
    html_message['To'] = doctor_email

    # Connect to Gmail SMTP server and send the email
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, doctor_email, html_message.as_string())
        print(f"Email sent to Dr. {doctor_name} ({doctor_email}) with subject: {subject}")

def send_email_to_patient(sender_email, sender_password, patient_email, patient_name, appointment_time):
    
    subject = "Your Appointment Confirmation"
    body = f"""
    <html>
        <body>
            <p>Dear {patient_name},</p>
            <p>Your appointment has been confirmed for the following time:</p>
            <p><b>Appointment Time:</b> {appointment_time}</p>
            <p>We look forward to seeing you!</p>
            <p>Best regards,<br>Your Appointment Team</p>
        </body>
    </html>
    """
    
    # Create the MIMEText email message with HTML content
    html_message = MIMEText(body, 'html')
    html_message['Subject'] = subject
    html_message['From'] = sender_email
    html_message['To'] = patient_email

    # Connect to Gmail SMTP server and send the email
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, patient_email, html_message.as_string())
        print(f"Email sent to {patient_name} ({patient_email}) with subject: {subject}")