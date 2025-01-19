from google.oauth2.credentials import Credentials as UserCredentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from jinja2 import Environment, FileSystemLoader
import os
import json
import base64
import firebase_admin
from firebase_admin import credentials, firestore

cred = credentials.Certificate('thelouwinstitute-firebase-adminsdk-94lop-b0dc9ff1e5.json')
firebase_admin.initialize_app(cred)

db = firestore.client()

# Gmail API scopes
GMAIL_SCOPES = ['https://www.googleapis.com/auth/gmail.send']

def get_credentials():
    if os.path.exists('auth_token.json'):
        with open('auth_token.json', 'r') as token_file:
            token_data = json.load(token_file)
        credentials = UserCredentials.from_authorized_user_info(token_data, GMAIL_SCOPES)
        if credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
    else:
        flow = InstalledAppFlow.from_client_secrets_file('credentials.json', GMAIL_SCOPES)
        credentials = flow.run_local_server(port=0)
        with open('auth_token.json', 'w') as token_file:
            token_file.write(credentials.to_json())
    return credentials

def create_email(from_email, to_email, subject, bcc_list):
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = from_email
    msg['To'] = to_email
    msg['bcc'] = ','.join(bcc_list)

    env = Environment(loader=FileSystemLoader('templates'))
    template = env.get_template('email.html') # note: email template here
    formatted_html_content = template.render()

    msg.attach(MIMEText(formatted_html_content, 'html'))

    return {'raw': base64.urlsafe_b64encode(msg.as_string().encode()).decode()}

def send_email(service, user_id, message):
    try:
        message = (service.users().messages().send(userId=user_id, body=message).execute())
        print(f'Email sent: {message}')
    except Exception as e:
        print(f'An error occurred: {e}')

bcc_emails = []
members = db.collection('members_get_in_touch').stream()
for member in members:
    email = member.to_dict().get('email')
    bcc_emails.append(email)

credentials = get_credentials()
service = build('gmail', 'v1', credentials=credentials)

from_email = 'connect.louwparty@gmail.com'
to_email = 'thelouwparty@googlegroups.com'
subject = 'The Final Curtain Call for The Louw Party' # note: subject here

email_message = create_email(from_email, to_email, subject, bcc_emails)
send_email(service, 'me', email_message)