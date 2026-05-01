import os.path
import io
import json
from google.auth.transport.requests import Request
from google.oauth2 import service_account
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

class GDriveConnector:
    def __init__(self):
        self.creds = self._authenticate()
        self.service = build('drive', 'v3', credentials=self.creds)

    def _authenticate(self):
        # 1. Try Service Account (Best for Cloud/Production)
        service_account_info = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
        if service_account_info:
            try:
                info = json.loads(service_account_info)
                return service_account.Credentials.from_service_account_info(info, scopes=SCOPES)
            except Exception as e:
                print(f"Service account auth failed: {e}")

        # 2. Fallback to OAuth (Best for Local Development)
        token_path = os.getenv("TOKEN_PATH", "data/credentials/token.json")
        creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "data/credentials/credentials.json")
        
        creds = None
        if os.path.exists(token_path):
            creds = Credentials.from_authorized_user_file(token_path, SCOPES)
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists(creds_path):
                    raise FileNotFoundError("No valid credentials found (Service Account or OAuth).")
                flow = InstalledAppFlow.from_client_secrets_file(creds_path, SCOPES)
                creds = flow.run_local_server(port=0)
            
            # Save the token for next time (Local only)
            if not os.getenv("STREAMLIT_CLOUD"):
                os.makedirs(os.path.dirname(token_path), exist_ok=True)
                with open(token_path, 'w') as token:
                    token.write(creds.to_json())
        return creds

    def list_files(self, query=None):
        if not query:
            query = "mimeType = 'application/pdf' or mimeType = 'application/vnd.google-apps.document' or mimeType = 'text/plain'"
        
        results = self.service.files().list(
            q=query, pageSize=100, fields="nextPageToken, files(id, name, mimeType)").execute()
        return results.get('files', [])

    def download_file(self, file_id, mime_type):
        if mime_type == 'application/vnd.google-apps.document':
            request = self.service.files().export_media(fileId=file_id, mimeType='text/plain')
        else:
            request = self.service.files().get_media(fileId=file_id)
        
        file_content = io.BytesIO()
        downloader = MediaIoBaseDownload(file_content, request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()
        return file_content.getvalue()
