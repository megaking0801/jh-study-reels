"""抓 IG 每支 Reels 的成效，寫到 insights.json 並印出表格。用法：python3 insights.py（token 在 ig_token.txt）"""
import json, os, sys, datetime, urllib.request, urllib.parse
HOST, API = "https://graph.facebook.com", "v25.0"
HERE = os.path.dirname(os.path.abspath(__file__))
TOKEN = open(os.path.join(HERE, "ig_token.txt")).read().strip()
UID = os.environ.get("IG_USER_ID", "17841466093914816")

def get(path, **p):
    p["access_token"] = TOKEN
    try:
        with urllib.request.urlopen(f"{HOST}/{API}/{path}?" + urllib.parse.urlencode(p), timeout=60) as r: return json.load(r)
    except urllib.error.HTTPError as e:
        return {"error": e.read().decode()[:300]}

METRICS = ["views", "reach", "likes", "comments", "shares", "saved", "total_interactions",
           "ig_reels_avg_watch_time", "ig_reels_video_view_total_time"]
media = get(f"{UID}/media", fields="id,caption,timestamp,media_product_type,permalink,like_count,comments_count", limit=50)
if "error" in media: print("media list failed:", media["error"]); sys.exit(0)
rows = []
for m in media.get("data", []):
    row = {"id": m["id"], "time": m["timestamp"], "title": (m.get("caption") or "").split("\n")[0][:30],
           "like_count": m.get("like_count"), "comments_count": m.get("comments_count"), "permalink": m.get("permalink")}
    r = get(f"{m['id']}/insights", metric=",".join(METRICS))
    if "error" in r:
        for k in METRICS:   # 有的指標不支援就逐個試
            one = get(f"{m['id']}/insights", metric=k)
            if "error" in one: row[k] = None
            else: row[k] = one["data"][0]["values"][0]["value"] if one.get("data") else None
    else:
        for d in r.get("data", []): row[d["name"]] = d["values"][0]["value"]
    rows.append(row)
acct = get(f"{UID}", fields="followers_count,follows_count,media_count")
out = {"fetched_at": datetime.datetime.utcnow().isoformat() + "Z", "account": acct, "media": rows}
json.dump(out, open(os.path.join(HERE, "insights.json"), "w"), ensure_ascii=False, indent=1)
print("account:", acct)
for x in rows:
    print(x["time"][:16], x["title"], {k: x.get(k) for k in METRICS})
