"""上傳長片到 YouTube（一次性）。素材從 GitHub Release「longform-1」下載到 longform/。
環境變數：YT_CLIENT_ID、YT_CLIENT_SECRET、YT_REFRESH_TOKEN、LONG_PRIVACY（預設 unlisted）"""
import json, os
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
H = os.path.dirname(os.path.abspath(__file__)); D = os.path.join(H, "longform")
m = json.load(open(os.path.join(D, "meta.json"), encoding="utf-8"))
creds = Credentials(None, refresh_token=os.environ["YT_REFRESH_TOKEN"], token_uri="https://oauth2.googleapis.com/token",
    client_id=os.environ["YT_CLIENT_ID"], client_secret=os.environ["YT_CLIENT_SECRET"],
    scopes=["https://www.googleapis.com/auth/youtube.upload", "https://www.googleapis.com/auth/youtube.readonly"])
api = build("youtube", "v3", credentials=creds, cache_discovery=False)
priv = os.environ.get("LONG_PRIVACY", "unlisted")
body = {"snippet": {"title": m["title"][:100], "description": m["description"], "tags": m["tags"], "categoryId": "27",
                    "defaultLanguage": "zh-Hant", "defaultAudioLanguage": "zh-Hant"},
        "status": {"privacyStatus": priv, "selfDeclaredMadeForKids": False, "containsSyntheticMedia": False, "embeddable": True},
        "paidProductPlacementDetails": {"hasPaidProductPlacement": False}}
req = api.videos().insert(part="snippet,status,paidProductPlacementDetails", body=body,
        media_body=MediaFileUpload(os.path.join(D, m["video"]), mimetype="video/mp4", resumable=True))
resp = None
while resp is None: _, resp = req.next_chunk()
vid = resp["id"]; print("影片上傳完成：https://youtu.be/" + vid, "隱私：", resp["status"]["privacyStatus"])
try:
    api.thumbnails().set(videoId=vid, media_body=MediaFileUpload(os.path.join(D, m["thumb"]), mimetype="image/png")).execute(); print("封面已設定")
except Exception as e: print("封面設定失敗（頻道可能未驗證）：", e)
