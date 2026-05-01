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
        # 1. Force check Streamlit Secrets first (for Cloud)
        service_account_info = None
        try:
            import streamlit as st
            if "GOOGLE_SERVICE_ACCOUNT_JSON" in st.secrets:
                service_account_info = st.secrets["GOOGLE_SERVICE_ACCOUNT_JSON"]
        except: pass

        # 2. Fallback to Environment Variable
        if not service_account_info:
            service_account_info = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")

        if service_account_info:
            try:
                # If it's a string, parse it. If it's already a dict, use it.
                if isinstance(service_account_info, str):
                    info = json.loads(service_account_info)
                else:
                    info = dict(service_account_info)
                
                # FIX: Ensure private key has correct newline characters and no extra quotes
                if "private_key" in info:
                    key = info["private_key"].strip()
                    # Remove any accidental wrapping quotes inside the JSON string
                    if (key.startswith('"') and key.endswith('"')) or (key.startswith("'") and key.endswith("'")):
                        key = key[1:-1]
                    
                    key = key.replace("\\n", "\n")
                    
                    # Ensure headers are intact
                    if "-----BEGIN PRIVATE KEY-----" not in key:
                        raise Exception("Private key is missing the '-----BEGIN PRIVATE KEY-----' header.")
                    
                    info["private_key"] = key
                    
                return service_account.Credentials.from_service_account_info(info, scopes=SCOPES)
            except Exception as e:
                raise Exception(f"Service Account Error: {str(e)} (Check for missing headers or extra spaces)")

        # 3. Last Resort: Local OAuth
        token_path = os.getenv("TOKEN_PATH", "data/credentials/token.json")
        creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "data/credentials/credentials.json")
        
        if os.path.exists(token_path):
            return Credentials.from_authorized_user_file(token_path, SCOPES)
        
        if os.path.exists(creds_path):
            flow = InstalledAppFlow.from_client_secrets_file(creds_path, SCOPES)
            return flow.run_local_server(port=0)
            
        raise Exception("No credentials found. Please add GOOGLE_SERVICE_ACCOUNT_JSON to Streamlit Secrets.")

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
