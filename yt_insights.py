"""每日抓 YouTube Analytics：各影片（近 28 天）觀看、平均觀看秒、平均觀看比例、讚、留言、分享、訂閱增減。
需要權杖含 yt-analytics.readonly（沒有就印出提示並正常結束，不讓排程失敗）。
環境變數：YT_CLIENT_ID、YT_CLIENT_SECRET、YT_REFRESH_TOKEN。輸出 yt_insights.json、yt_insights_history.csv。"""
import os, sys, json, csv, datetime

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

HERE = os.path.dirname(os.path.abspath(__file__))
SCOPES = ["https://www.googleapis.com/auth/youtube.readonly",
          "https://www.googleapis.com/auth/yt-analytics.readonly"]

creds = Credentials(None, refresh_token=os.environ["YT_REFRESH_TOKEN"], token_uri="https://oauth2.googleapis.com/token",
                    client_id=os.environ["YT_CLIENT_ID"], client_secret=os.environ["YT_CLIENT_SECRET"])
yta = build("youtubeAnalytics", "v2", credentials=creds, cache_discovery=False)
yt = build("youtube", "v3", credentials=creds, cache_discovery=False)

today = datetime.date.today()
start = (today - datetime.timedelta(days=28)).isoformat()
end = today.isoformat()
M = "views,estimatedMinutesWatched,averageViewDuration,averageViewPercentage,likes,comments,shares,subscribersGained,subscribersLost"

try:
    per = yta.reports().query(ids="channel==MINE", startDate=start, endDate=end, metrics=M,
                              dimensions="video", sort="-views", maxResults=200).execute()
    daily = yta.reports().query(ids="channel==MINE", startDate=start, endDate=end,
                                metrics="views,estimatedMinutesWatched,subscribersGained", dimensions="day", sort="day").execute()
except HttpError as e:
    print("YouTube Analytics 讀取失敗（多半是權杖缺 yt-analytics.readonly 或沒啟用 YouTube Analytics API）：", e.status_code, e.reason)
    sys.exit(0)

cols = [h["name"] for h in per.get("columnHeaders", [])]
rows = [dict(zip(cols, r)) for r in per.get("rows", [])]
ids = [r["video"] for r in rows]
titles = {}
for i in range(0, len(ids), 50):
    for it in yt.videos().list(part="snippet", id=",".join(ids[i:i + 50])).execute().get("items", []):
        titles[it["id"]] = it["snippet"]["title"]
for r in rows:
    r["title"] = titles.get(r["video"], "")

now = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
json.dump({"fetched_at": now, "range": [start, end], "videos": rows,
           "daily": [dict(zip([h["name"] for h in daily.get("columnHeaders", [])], r)) for r in daily.get("rows", [])]},
          open(os.path.join(HERE, "yt_insights.json"), "w"), ensure_ascii=False, indent=1)

hist = os.path.join(HERE, "yt_insights_history.csv")
new = not os.path.exists(hist)
with open(hist, "a", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    if new:
        w.writerow(["fetched_at", "video", "title"] + cols[1:])
    for r in rows:
        w.writerow([now, r["video"], r["title"]] + [r.get(c, "") for c in cols[1:]])
print(f"YouTube Analytics：{len(rows)} 支影片，{start} 到 {end}")
