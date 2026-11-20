# jh-study-reels
@jh.study.tw 的 Reels 自動排程。`queue.json` 是發文佇列（date、video_url、caption、status），
`.github/workflows/publish.yml` 每天 20:00（台灣）跑 `publish_reel.py`，發第一支到期的 pending 影片。
影片放 `videos/`，由 GitHub Pages 對外提供網址。權杖存在 repo secret `IG_TOKEN`，不放在檔案裡。

## YouTube Shorts
同一支影片也由 `yt_upload.py` 上傳到 YouTube（Shorts 自動判定：9:16、3 分鐘內）。
Secrets：`YT_CLIENT_ID`、`YT_CLIENT_SECRET`、`YT_REFRESH_TOKEN`。佇列欄位：`video_file`、`yt_title`、`yt_description`、`yt_tags`、`yt_status`。
手動執行 workflow 可選 mode：check（只驗證授權）、yt-test（不公開測試上傳）、normal（照排程發）。
