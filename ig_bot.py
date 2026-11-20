"""留言關鍵字 → 私訊重點整理（Instagram 私訊回覆留言）。
用法：python3 ig_bot.py [--check] [--dry]
- 讀最近 15 則貼文的留言；留言含關鍵字 → 對該則留言發「私訊回覆」(recipient.comment_id)。
- 重點整理文字放在環境變數 BOT_RECAPS（JSON：{"影子":"文字",...}），不放進公開 repo。
- 已處理的留言 id 存在 bot_state.json，避免重複私訊。
- 每則留言只能私訊回覆一次（Meta 規定，且須在留言後 7 天內）。"""
import json, os, sys, urllib.request, urllib.parse
HOST, API = "https://graph.facebook.com", "v25.0"
HERE = os.path.dirname(os.path.abspath(__file__))
STATE = os.path.join(HERE, "bot_state.json")
IG = os.environ.get("IG_USER_ID", "17841466093914816")
TOKEN = os.environ.get("IG_BOT_TOKEN") or os.environ.get("IG_TOKEN", "")
RECAPS = json.loads(os.environ.get("BOT_RECAPS") or "{}")
DRY, CHECK = "--dry" in sys.argv, "--check" in sys.argv

def call(method, path, **params):
    body = None
    if method == "POST":
        body = urllib.parse.urlencode({k: v if isinstance(v, str) else json.dumps(v) for k, v in {**params, "access_token": TOKEN}.items()}).encode()
        url = f"{HOST}/{API}/{path}"
    else:
        url = f"{HOST}/{API}/{path}?" + urllib.parse.urlencode({**params, "access_token": TOKEN})
    try:
        with urllib.request.urlopen(urllib.request.Request(url, data=body, method=method), timeout=60) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        return {"error": e.read().decode()[:400]}

def main():
    st = json.load(open(STATE)) if os.path.exists(STATE) else {"done": []}
    done = set(st["done"])
    media = call("GET", f"{IG}/media", fields="id,caption,timestamp", limit="15")
    if "error" in media: print("media error:", media["error"]); return
    print("recent media:", len(media.get("data", [])), "| keywords:", list(RECAPS))
    sent = 0
    for m in media.get("data", []):
        cs = call("GET", f"{m['id']}/comments", fields="id,text,username,timestamp", limit="50")
        if "error" in cs: print("comments error:", cs["error"]); continue
        for c in cs.get("data", []):
            if c["id"] in done: continue
            text = c.get("text", "")
            kw = next((k for k in RECAPS if k in text), None)
            if CHECK: print(" comment", c["id"], repr(text[:30]), "->", kw); continue
            if not kw: done.add(c["id"]); continue
            print("reply to", c.get("username"), "kw", kw)
            if DRY: continue
            r = call("POST", f"{IG}/messages", recipient={"comment_id": c["id"]}, message={"text": RECAPS[kw]})
            print(" ->", str(r)[:200])
            if "error" not in r: sent += 1
            done.add(c["id"])  # 失敗也記，避免每 10 分鐘重複打；錯誤看 log
    if not (DRY or CHECK):
        json.dump({"done": sorted(done)[-2000:]}, open(STATE, "w"))
    print("sent:", sent)

if __name__ == "__main__": main()
