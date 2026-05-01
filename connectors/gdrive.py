import os.path
import io
import json
import base64
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
        # 1. Check Streamlit Secrets (for Cloud)
        service_account_info = None
        try:
            import streamlit as st
            # Try Base64 First (The Bulletproof Way)
            if "GOOGLE_SERVICE_ACCOUNT_B64" in st.secrets:
                b64_data = st.secrets["GOOGLE_SERVICE_ACCOUNT_B64"]
                decoded_data = base64.b64decode(b64_data).decode('utf-8')
                service_account_info = json.loads(decoded_data)
            # Fallback to JSON String
            elif "GOOGLE_SERVICE_ACCOUNT_JSON" in st.secrets:
                service_account_info = st.secrets["GOOGLE_SERVICE_ACCOUNT_JSON"]
        except: pass

        if not service_account_info:
            service_account_info = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")

        if service_account_info:
            try:
                # Parse if string, use if dict
                if isinstance(service_account_info, str):
                    info = json.loads(service_account_info)
                else:
                    info = dict(service_account_info)
                
                # Fix escaped newlines
                if "private_key" in info:
                    info["private_key"] = info["private_key"].replace("\\n", "\n")
                
                return service_account.Credentials.from_service_account_info(info, scopes=SCOPES)
            except Exception as e:
                raise Exception(f"Service Account Auth Failed: {e}")

        # 2. Last Resort: Local OAuth
        token_path = "data/credentials/token.json"
        creds_path = "data/credentials/credentials.json"
        
        if os.path.exists(token_path):
            return Credentials.from_authorized_user_file(token_path, SCOPES)
        
        if os.path.exists(creds_path):
            flow = InstalledAppFlow.from_client_secrets_file(creds_path, SCOPES)
            return flow.run_local_server(port=0)
            
        raise Exception("No credentials found. Please add GOOGLE_SERVICE_ACCOUNT_B64 or GOOGLE_SERVICE_ACCOUNT_JSON to Streamlit Secrets.")

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
