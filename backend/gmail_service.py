"""
Gmail Integration Service for FlowForge
OAuth 2.0 authentication with real Gmail API access
"""
import os
import json
import base64
from typing import Optional, List, Dict, Any
from pathlib import Path

# Gmail API imports (with fallback for when not installed)
try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    GMAIL_AVAILABLE = True
except ImportError:
    GMAIL_AVAILABLE = False

# Scopes for Gmail API - read-only access
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

# Paths for credentials
BACKEND_DIR = Path(__file__).parent
CREDENTIALS_FILE = BACKEND_DIR / "credentials.json"
TOKEN_FILE = BACKEND_DIR / "token.json"


class GmailService:
    """Gmail API wrapper with OAuth 2.0"""
    
    def __init__(self):
        self.service = None
        self.authenticated = False
        self.user_email = None
        
    def is_available(self) -> bool:
        """Check if Gmail API libraries are installed"""
        return GMAIL_AVAILABLE
    
    def has_credentials(self) -> bool:
        """Check if credentials.json exists"""
        return CREDENTIALS_FILE.exists()
    
    def is_authenticated(self) -> bool:
        """Check if we have valid token"""
        if not GMAIL_AVAILABLE:
            return False
        if TOKEN_FILE.exists():
            try:
                creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
                return creds and creds.valid
            except:
                return False
        return False
    
    def get_auth_url(self) -> Optional[str]:
        """Get OAuth URL for user to authenticate (for manual flow)"""
        if not GMAIL_AVAILABLE or not self.has_credentials():
            return None
        try:
            flow = InstalledAppFlow.from_client_secrets_file(
                str(CREDENTIALS_FILE), SCOPES
            )
            flow.redirect_uri = 'urn:ietf:wg:oauth:2.0:oob'
            auth_url, _ = flow.authorization_url(prompt='consent')
            return auth_url
        except Exception as e:
            print(f"[GMAIL] Auth URL error: {e}")
            return None
    
    def authenticate_with_code(self, auth_code: str) -> bool:
        """Exchange auth code for token"""
        if not GMAIL_AVAILABLE or not self.has_credentials():
            return False
        try:
            flow = InstalledAppFlow.from_client_secrets_file(
                str(CREDENTIALS_FILE), SCOPES
            )
            flow.redirect_uri = 'urn:ietf:wg:oauth:2.0:oob'
            flow.fetch_token(code=auth_code)
            creds = flow.credentials
            
            # Save token
            with open(TOKEN_FILE, 'w') as token:
                token.write(creds.to_json())
            
            self.authenticated = True
            return True
        except Exception as e:
            print(f"[GMAIL] Auth code exchange error: {e}")
            return False
    
    def authenticate(self) -> bool:
        """Authenticate with Gmail - uses existing token or initiates OAuth flow"""
        if not GMAIL_AVAILABLE:
            print("[GMAIL] Google API libraries not installed")
            return False
            
        if not self.has_credentials():
            print("[GMAIL] No credentials.json found")
            return False
        
        creds = None
        
        # Check for existing token
        if TOKEN_FILE.exists():
            try:
                creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
            except Exception as e:
                print(f"[GMAIL] Token load error: {e}")
        
        # Refresh or get new credentials
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except Exception as e:
                    print(f"[GMAIL] Token refresh error: {e}")
                    creds = None
            
            if not creds:
                try:
                    # This will open browser for OAuth
                    flow = InstalledAppFlow.from_client_secrets_file(
                        str(CREDENTIALS_FILE), SCOPES
                    )
                    creds = flow.run_local_server(port=8080, open_browser=True)
                except Exception as e:
                    print(f"[GMAIL] OAuth flow error: {e}")
                    return False
            
            # Save the credentials
            with open(TOKEN_FILE, 'w') as token:
                token.write(creds.to_json())
        
        try:
            self.service = build('gmail', 'v1', credentials=creds)
            # Get user email
            profile = self.service.users().getProfile(userId='me').execute()
            self.user_email = profile.get('emailAddress')
            self.authenticated = True
            print(f"[GMAIL] Authenticated as {self.user_email}")
            return True
        except Exception as e:
            print(f"[GMAIL] Service build error: {e}")
            return False
    
    def disconnect(self) -> bool:
        """Remove saved token to disconnect Gmail"""
        try:
            if TOKEN_FILE.exists():
                TOKEN_FILE.unlink()
            self.service = None
            self.authenticated = False
            self.user_email = None
            return True
        except Exception as e:
            print(f"[GMAIL] Disconnect error: {e}")
            return False
    
    def get_status(self) -> Dict:
        """Get current Gmail connection status"""
        return {
            "available": GMAIL_AVAILABLE,
            "has_credentials": self.has_credentials(),
            "authenticated": self.is_authenticated(),
            "user_email": self.user_email,
            "needs_setup": not self.has_credentials(),
            "needs_auth": self.has_credentials() and not self.is_authenticated()
        }
    
    def fetch_emails(self, max_results: int = 5) -> List[Dict]:
        """Fetch latest emails from Gmail"""
        if not self.authenticated or not self.service:
            # Try to authenticate first
            if not self.authenticate():
                return []
        
        try:
            # Get message list
            results = self.service.users().messages().list(
                userId='me',
                maxResults=max_results,
                labelIds=['INBOX']
            ).execute()
            
            messages = results.get('messages', [])
            emails = []
            
            for msg in messages:
                try:
                    # Get full message
                    message = self.service.users().messages().get(
                        userId='me',
                        id=msg['id'],
                        format='full'
                    ).execute()
                    
                    # Extract headers
                    headers = message.get('payload', {}).get('headers', [])
                    subject = next((h['value'] for h in headers if h['name'].lower() == 'subject'), 'No Subject')
                    sender = next((h['value'] for h in headers if h['name'].lower() == 'from'), 'Unknown')
                    date = next((h['value'] for h in headers if h['name'].lower() == 'date'), '')
                    
                    # Get snippet
                    snippet = message.get('snippet', '')
                    
                    # Get body
                    body = self._extract_body(message)
                    
                    emails.append({
                        "id": msg['id'],
                        "subject": subject,
                        "sender": sender,
                        "date": date,
                        "snippet": snippet,
                        "body": body[:1000] if body else snippet  # Limit body size
                    })
                except Exception as e:
                    print(f"[GMAIL] Error fetching message {msg['id']}: {e}")
                    continue
            
            return emails
            
        except Exception as e:
            print(f"[GMAIL] Fetch error: {e}")
            return []
    
    def _extract_body(self, message: Dict) -> str:
        """Extract plain text body from Gmail message"""
        try:
            payload = message.get('payload', {})
            
            # Check for simple body
            if 'body' in payload and payload['body'].get('data'):
                return base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8')
            
            # Check parts
            parts = payload.get('parts', [])
            for part in parts:
                if part.get('mimeType') == 'text/plain':
                    data = part.get('body', {}).get('data')
                    if data:
                        return base64.urlsafe_b64decode(data).decode('utf-8')
            
            # Fallback to snippet
            return message.get('snippet', '')
            
        except Exception as e:
            return message.get('snippet', '')


# Singleton instance
gmail_service = GmailService()


def get_gmail_status() -> Dict:
    """Get Gmail service status"""
    return gmail_service.get_status()


def authenticate_gmail() -> bool:
    """Authenticate with Gmail"""
    return gmail_service.authenticate()


def disconnect_gmail() -> bool:
    """Disconnect Gmail"""
    return gmail_service.disconnect()


def fetch_gmail_emails(max_results: int = 5) -> List[Dict]:
    """Fetch emails from Gmail"""
    return gmail_service.fetch_emails(max_results)


def format_email_for_workflow(email: Dict) -> str:
    """Format email for workflow input"""
    return f"""Subject: {email.get('subject', 'No Subject')}
From: {email.get('sender', 'Unknown')}
Date: {email.get('date', '')}

{email.get('body', email.get('snippet', ''))}"""
