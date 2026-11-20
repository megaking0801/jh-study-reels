# jh-study-reels
@jh.study.tw 的 Reels 自動排程。`queue.json` 是發文佇列（date、video_url、caption、status），
`.github/workflows/publish.yml` 每天 20:00（台灣）跑 `publish_reel.py`，發第一支到期的 pending 影片。
影片放 `videos/`，由 GitHub Pages 對外提供網址。權杖存在 repo secret `IG_TOKEN`，不放在檔案裡。
