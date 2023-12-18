import os.path
import json
from google.auth import credentials
import googleapiclient.errors
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# APIキーとサービス名、バージョンを設定
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"

# 認証情報が含まれるJSONファイルの名前とスコープを設定
CLIENT_SECRETS_FILE = "CLIENTSECRET.json"
SCOPES = ["https://www.googleapis.com/auth/youtube"]

class google_get_credential:
    def get_credentials():
        creds = None
        # The file token.json stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        if os.path.exists("token.json"):
            creds = Credentials.from_authorized_user_file("token.json", SCOPES)
        # 認証情報が存在しないか有効期限切れの場合、トークンリフレッシュまたは再認証を行う
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    CLIENT_SECRETS_FILE, SCOPES
                )
                creds = flow.run_local_server(port=0)
        # token.jsonに認証情報を保存
        with open("token.json", "w") as token:
          token.write(creds.to_json())
      
        # サービスオブジェクトを作成する
        youtube = googleapiclient.discovery.build(
            YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, credentials=creds)
        # サービスオブジェクトを返す
        return youtube
pass
