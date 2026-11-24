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
            if "error" in one:
                row[k] = None; row.setdefault("errors", {})[k] = one["error"][:200]
            else: row[k] = one["data"][0]["values"][0]["value"] if one.get("data") else None
    else:
        for d in r.get("data", []): row[d["name"]] = d["values"][0]["value"]
    rows.append(row)
acct = get(f"{UID}", fields="followers_count,follows_count,media_count")
out = {"fetched_at": datetime.datetime.utcnow().isoformat() + "Z", "account": acct, "media": rows}
json.dump(out, open(os.path.join(HERE, "insights.json"), "w"), ensure_ascii=False, indent=1)
print("account:", acct)
for x in rows[:1]: print("sample errors:", json.dumps(x.get("errors"), ensure_ascii=False)[:900])
for x in rows:
    print(x["time"][:16], x["title"], {k: x.get(k) for k in METRICS})

# ---- 每日快照：附加到 insights_history.csv（日期、帳號追蹤數、每支的指標），用來看 24h／72h 的成長 ----
import csv
hist = os.path.join(HERE, "insights_history.csv")
new = not os.path.exists(hist)
with open(hist, "a", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    if new: w.writerow(["fetched_at", "followers", "media_id", "posted_at", "title", "views", "reach", "likes", "comments", "shares", "saved", "avg_watch_ms"])
    for x in rows:
        w.writerow([out["fetched_at"], (acct or {}).get("followers_count"), x["id"], x["time"], x["title"], x.get("views"), x.get("reach"), x.get("likes"),
                    x.get("comments"), x.get("shares"), x.get("saved"), x.get("ig_reels_avg_watch_time")])
print("history rows appended:", len(rows))
