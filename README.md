# 稅務日報 Taiwan Tax Daily

每日彙整財政部、臺北、北區、中區、南區、高雄國稅局的官方 RSS，保留歷史資料，使用 GitHub Actions 更新並部署 GitHub Pages。

網站：https://scott22489-svg.github.io/taiwan-tax-daily/

## 運作方式

每天台灣時間 07:00（UTC 前一天 23:00）執行：下載 RSS → 檢查與分類 → 依來源網址去重 → 保存 `data/articles.json` → 建置靜態網站 → 發布 Pages。GitHub 排程可能延遲，不保證準點。

- 支援全文關鍵字（標題及節錄）、稅別、來源、最近 7／30／90 天篩選與分頁。
- RSS 不再提供的舊文章仍保留。首次匯入僅涵蓋來源目前提供的資料，非完整歷年資料庫。
- 同網址不重複新增，來源內容變更時更新節錄並保留首次收錄時間。不同機關轉載的不同網址各自保留。
- 摘要目前是 **官方 RSS 內容前 200 字節錄**，不是 AI 摘要。分類為關鍵字規則，不能視為法律判斷。
- 部分來源失敗時保留該來源歷史文章並顯示提示；全部失敗則停止部署，維持上次正常網站。超過 48 小時未更新時網站提示資料可能過期。
- 不需要額外 API 金鑰、資料庫或持續開機的個人電腦。
- AI 摘要、YouTube 與 LINE 尚未啟用。先前討論曾舉例提及，後續需另設定 API、頻道及通知對象。

## GitHub 設定

1. 使用公開儲存庫（GitHub Free 支援公開儲存庫 Pages）。
2. `Settings → Pages → Build and deployment → Source` 選擇 **GitHub Actions**。
3. 在 `Actions → 每日稅務更新與發布 → Run workflow` 可手動更新。
4. 首次成功部署後，開啟上方網站網址。

工作流程僅授予更新工作 `contents: write`、發布工作 `pages: write` 與 `id-token: write`。未使用付費服務或任何密鑰。若組織政策或分支保護禁止機器人寫入 main，需要另外調整提交流程。

`data/articles.json` 保存內容與更新狀態並每天提交，方便回溯。只發布 `dist/` 公開檔案，不把設定或未來的密鑰部署到網站。公開儲存庫長期無活動時排程可能被 GitHub 停用；此流程正常時每日資料提交會產生活動，仍應注意 GitHub Actions 失敗通知。

## 本機執行（Python 3.12，無額外套件）

```sh
python -m unittest discover -s tests -v
python scripts/update.py
python scripts/build.py
python -m http.server 8765 --directory dist --bind 127.0.0.1
```

開啟 http://127.0.0.1:8765 。請透過 HTTP 預覽；直接開啟 HTML 檔案時，瀏覽器可能禁止讀取 JSON。

來源設定：`config/sources.json`。網站介面：`web/`。排程：`.github/workflows/daily.yml`。

## 官方參考

- [GitHub Pages 自訂 Actions 工作流程](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages)
- [GitHub Actions 排程事件與限制](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule)
- [財政部 RSS](https://www.mof.gov.tw/Rss)

文章以各機關原文為準，網站每則消息均保留來源連結。
