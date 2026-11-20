"""把 queue.json 裡到期的影片上傳成 YouTube Shorts（YouTube Data API v3）。
用法：python3 yt_upload.py [--dry] [--check] [--test]
  --check  只驗證授權，印出頻道名稱
  --test   把佇列第一支用「不公開」上傳，確認新專案上傳不會被鎖成私人（不改佇列）
需要環境變數：YT_CLIENT_ID、YT_CLIENT_SECRET、YT_REFRESH_TOKEN（存在 GitHub Secrets）。
影片直接從 repo 的 video_file 上傳（9:16、3 分鐘內 → 自動算 Shorts）。"""
import json, os, sys, datetime
from google.oauth2.credentials import Credentials
from google.auth.exceptions import RefreshError
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

HERE = os.path.dirname(os.path.abspath(__file__))
QUEUE = os.environ.get("IG_QUEUE", os.path.join(HERE, "queue.json"))
TZ = datetime.timezone(datetime.timedelta(hours=8))
DRY, CHECK, TEST = ("--dry" in sys.argv, "--check" in sys.argv, "--test" in sys.argv)

def yt():
    creds = Credentials(None, refresh_token=os.environ["YT_REFRESH_TOKEN"],
                        token_uri="https://oauth2.googleapis.com/token",
                        client_id=os.environ["YT_CLIENT_ID"], client_secret=os.environ["YT_CLIENT_SECRET"],
                        scopes=["https://www.googleapis.com/auth/youtube.upload",
                                "https://www.googleapis.com/auth/youtube.readonly"])
    try:
        return build("youtube", "v3", credentials=creds, cache_discovery=False)
    except RefreshError as e:
        raise SystemExit(f"YouTube 授權失效（invalid_grant），需要重新授權：{e}")

def upload(api, item, privacy):
    body = {
        "snippet": {"title": item.get("yt_title", item["title"])[:100],
                    "description": item.get("yt_description", item["caption"]),
                    "tags": item.get("yt_tags", ["國中數學", "會考", "段考"]),
                    "categoryId": "27", "defaultLanguage": "zh-Hant", "defaultAudioLanguage": "zh-Hant"},
        "status": {"privacyStatus": privacy, "selfDeclaredMadeForKids": False,
                   "containsSyntheticMedia": False, "embeddable": True},
        "paidProductPlacementDetails": {"hasPaidProductPlacement": False},
    }
    media = MediaFileUpload(os.path.join(HERE, item["video_file"]), mimetype="video/mp4", resumable=True)
    req = api.videos().insert(part="snippet,status,paidProductPlacementDetails", body=body, media_body=media)
    resp = None
    while resp is None:
        _, resp = req.next_chunk()
    print("YouTube 上傳完成：", resp["id"], "隱私：", resp["status"]["privacyStatus"])
    return resp

def main():
    if CHECK:
        r = yt().channels().list(part="snippet", mine=True).execute()
        print("YouTube OK:", [c["snippet"]["title"] for c in r.get("items", [])]); return
    q = json.load(open(QUEUE))
    if TEST:
        r = upload(yt(), q[0], "unlisted")
        print("測試網址： https://youtube.com/shorts/" + r["id"]); return
    now = datetime.datetime.now(TZ).replace(tzinfo=None)
    due = lambda x: now >= datetime.datetime.fromisoformat(x["date"] + "T" + x.get("time", "18:00"))
    item = next((x for x in q if x.get("yt_status", "pending") == "pending" and "video_file" in x and due(x)), None)
    if not item: print("YouTube：今天沒有到期的影片"); return
    print("YouTube 準備發：", item["title"])
    if DRY: return
    r = upload(yt(), item, "public")
    item.update(yt_status="posted", yt_id=r["id"], yt_posted_at=datetime.datetime.now(TZ).isoformat(timespec="seconds"))
    json.dump(q, open(QUEUE, "w"), ensure_ascii=False, indent=1)

if __name__ == "__main__": main()
