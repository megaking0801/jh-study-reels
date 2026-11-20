"""每天自動發 Reels（Instagram API with Instagram Login）。
用法：python3 publish_reel.py [--dry]
讀 queue.json（依 date 排程，status=pending），今天或之前到期的第一支就發；發完把 status 改成 posted。
需要：IG_USER_ID（預設 17841466093914816 = @jh.study.tw）、token 檔（預設 ./ig_token.txt，內容是系統用戶永久權杖，不需續期）。
影片必須是公開網址（video_url），Meta 會自己去抓。"""
import json, os, sys, time, datetime, urllib.request, urllib.parse
HOST = "https://graph.facebook.com"
API = "v25.0"
HERE = os.path.dirname(os.path.abspath(__file__))
TOKEN_FILE = os.environ.get("IG_TOKEN_FILE", os.path.join(HERE, "ig_token.txt"))
QUEUE = os.environ.get("IG_QUEUE", os.path.join(HERE, "queue.json"))
IG_USER_ID = os.environ.get("IG_USER_ID", "17841466093914816")
DRY = "--dry" in sys.argv
CHECK = "--check" in sys.argv
TZ = datetime.timezone(datetime.timedelta(hours=8))  # 台灣時間

def call(method, path, token, **params):
    params["access_token"] = token
    url = f"{HOST}/{API}/{path}" if not path.startswith("http") else path
    data = urllib.parse.urlencode(params).encode() if method == "POST" else None
    if method == "GET": url += "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, data=data, method=method)
    try:
        with urllib.request.urlopen(req, timeout=60) as r: return json.load(r)
    except urllib.error.HTTPError as e:
        raise SystemExit(f"API error {e.code}: {e.read().decode()[:500]}")

def refresh_token(token):
    # 系統用戶權杖永不過期，不需續期
    return token

def main():
    token = open(TOKEN_FILE).read().strip()
    if CHECK:
        r = call("GET", IG_USER_ID, token, fields="username,media_count")
        print("token OK:", r); return
    q = json.load(open(QUEUE))
    now = datetime.datetime.now(TZ).replace(tzinfo=None)
    def due(x):  # date + time(台灣時間，預設 18:00) 已到
        return now >= datetime.datetime.fromisoformat(x["date"] + "T" + x.get("time", "18:00"))
    item = next((x for x in q if x["status"] == "pending" and due(x)), None)
    if not item: print("今天沒有到期的影片"); return
    print("準備發：", item["title"], item["video_url"])
    if DRY: return
    lim = call("GET", f"{IG_USER_ID}/content_publishing_limit", token, fields="quota_usage")
    print("quota:", lim)
    c = call("POST", f"{IG_USER_ID}/media", token, media_type="REELS", video_url=item["video_url"],
             caption=item["caption"], share_to_feed="true")
    cid = c["id"]
    for _ in range(10):  # 每分鐘查一次，最多 10 分鐘
        st = call("GET", cid, token, fields="status_code")
        print("status:", st.get("status_code"))
        if st.get("status_code") == "FINISHED": break
        if st.get("status_code") in ("ERROR", "EXPIRED"): raise SystemExit(f"container failed: {st}")
        time.sleep(60)
    else: raise SystemExit("處理逾時，沒有發出")
    pub = call("POST", f"{IG_USER_ID}/media_publish", token, creation_id=cid)
    item["status"] = "posted"; item["media_id"] = pub.get("id"); item["posted_at"] = datetime.datetime.now().isoformat(timespec="seconds")
    json.dump(q, open(QUEUE, "w"), ensure_ascii=False, indent=1)
    open(TOKEN_FILE, "w").write(refresh_token(token))
    print("已發布：", pub)

if __name__ == "__main__": main()
