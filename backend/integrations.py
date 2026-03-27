import json
import os
from typing import Optional, Dict, List

# Gmail API imports
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

DEMO_FILE = os.path.join(os.path.dirname(__file__), "..", "demo", "sample_emails.json")
CREDENTIALS_FILE = os.path.join(os.path.dirname(__file__), "credentials.json")
TOKEN_FILE = os.path.join(os.path.dirname(__file__), "token.json")

# Gmail API scope (read-only)
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

# Track which emails have been processed
processed_emails = set()


# ============== GMAIL API FUNCTIONS ==============

def get_gmail_service():
    """Authenticate and return Gmail API service"""
    creds = None
    
    # Load existing token if available
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    
    # If no valid credentials, authenticate
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(CREDENTIALS_FILE):
                raise FileNotFoundError("credentials.json not found. Download it from Google Cloud Console.")
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Save token for next run
        with open(TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())
    
    return build('gmail', 'v1', credentials=creds)


def fetch_latest_emails(max_results: int = 5) -> List[Dict]:
    """Fetch latest emails from Gmail"""
    try:
        service = get_gmail_service()
        
        # Get list of messages
        results = service.users().messages().list(
            userId='me',
            maxResults=max_results,
            labelIds=['INBOX']
        ).execute()
        
        messages = results.get('messages', [])
        
        if not messages:
            return []
        
        emails = []
        for msg in messages:
            # Get full message details
            message = service.users().messages().get(
                userId='me',
                id=msg['id'],
                format='metadata',
                metadataHeaders=['Subject', 'From']
            ).execute()
            
            # Extract subject from headers
            headers = message.get('payload', {}).get('headers', [])
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
            sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown')
            snippet = message.get('snippet', '')
            
            emails.append({
                'id': msg['id'],
                'subject': subject,
                'sender': sender,
                'snippet': snippet
            })
        
        return emails
    
    except FileNotFoundError as e:
        raise e
    except Exception as e:
        raise Exception(f"Gmail API error: {str(e)}")


def load_sample_emails() -> List[Dict]:
    """Load sample emails from JSON file"""
    try:
        with open(DEMO_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return get_default_emails()


def get_default_emails() -> List[Dict]:
    """Default emails if file not found"""
    return [
        {
            "id": 1,
            "subject": "URGENT: Production database is down",
            "sender": "ops@company.com",
            "body": "Our main production database has been unreachable for the past 15 minutes. All customer-facing services are affected. We need immediate action.",
            "urgency": "high"
        },
        {
            "id": 2,
            "subject": "Meeting follow-up: Q4 Planning",
            "sender": "sarah@company.com",
            "body": "Thanks for the great discussion today. Could you send me the slides and let me know your availability for a follow-up next week?",
            "urgency": "medium"
        },
        {
            "id": 3,
            "subject": "Quick question about the API",
            "sender": "developer@partner.com",
            "body": "Hey! I'm integrating with your API and noticed the /users endpoint returns a 404. Is this expected behavior or am I missing something?",
            "urgency": "medium"
        }
    ]


def get_next_mock_email() -> Optional[Dict]:
    """Get the next unprocessed mock email"""
    emails = load_sample_emails()
    
    for email in emails:
        if email['id'] not in processed_emails:
            processed_emails.add(email['id'])
            return email
    
    # If all processed, reset and start over
    processed_emails.clear()
    if emails:
        processed_emails.add(emails[0]['id'])
        return emails[0]
    
    return None


def reset_processed_emails():
    """Reset the processed emails tracker"""
    processed_emails.clear()


def format_email_for_input(email: Dict) -> str:
    """Format email dict as input string"""
    return f"""Subject: {email['subject']}
From: {email['sender']}

{email['body']}"""
