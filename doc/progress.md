# 專案進度

## 2026-09-07：LocWarp 上游同步啟動

- 已依 `locwarp-sync-upstream` 技能讀取同步規範、`doc/upstream-sync/README.md`、`doc/custom-feature-ledger.md` 及四個同步／驗證腳本。
- repository 內未找到實體 `AGENTS.md`；本次依對話提供的規範執行，並保留既有未提交的版本一致性紀錄。
- 初始檢查確認目前分支為 `custom/main`，遠端契約正確；工作樹原本只有既有的 `doc/progress.md` 變更，已安全保留後恢復。
- 已抓取 `upstream` 的 tags 與 prune；官方最新 release 為 `v0.2.196`，commit `271779b`，正規化版本與 `upstream/main:frontend/package.json` 均為 `0.2.196`。
- 抓取後 `custom/main...upstream/main` 分歧為 `24/4`；官方 tag 與 manifest 一致，未觸發版本阻擋。
- `scripts/rehearse-upstream.ps1 -SkipFetch` 已完成預演；官方 v0.2.196 與客製分支在 `backend/api/device.py`、`backend/requirements.txt`、`frontend/package-lock.json` 發生內容衝突，尚未修改工作樹。
- 正式同步已建立 `sync/upstream-v0.2.196`，並將本機 `main` 鏡像更新至官方 `271779b`；衝突仍只停留在同步分支。
- 衝突分析確認官方 v0.2.193 的 WiFi RemotePairing port 自動掃描需保留；客製 `WifiTunnelRuntimeError`／Python 3.13 錯誤映射、官方 v0.2.196 的 `pymobiledevice3` 11.2.0 相依升級與前端 lockfile 更新將在同步分支整合。
- 已用官方 tag `v0.2.196` 驗證並同步客製版本；`frontend/package.json`、`frontend/package-lock.json` 頂層 `version` 與 `packages[""].version` 均為 `0.2.196`。
- `scripts/check-extension-boundaries.ps1` 已通過；必要 custom extension 模組未遺失，也沒有重新滲回官方核心的受禁用實作。
- 2-opt regression 已通過：`5 passed`；第一次執行僅被 venv 的 xonsh console plugin 阻斷，改以 `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1` 重跑後成功。
- `scripts/verify.ps1` 已完整通過：extension boundaries、Backend Pyright（0 errors／warnings／informations）、Electron syntax、Frontend TypeScript 與 Vite production build；先前 build 失敗確認是舊 `node_modules`，乾淨 `npm ci` 對齊 MapLibre 6.6.0 後成功。
- Backend 完整測試 `19 passed`（含 extension 與 WiFi tunnel runtime）；本機 Mypy 安裝至既有 venv 後執行 `--ignore-missing-imports backend`，61 個 source files 無 issues。
- 已在 `sync/upstream-v0.2.196` 建立雙親 merge commit `3d271cf`，父 commit 為客製 `2d54421` 與官方 `271779b`；staged diff、空白與衝突標記檢查均通過。
- 已將 `sync/upstream-v0.2.196` 以 `--ff-only` 推進 `custom/main` 至 `6831504`；最終 rehearsal 通過：`custom/main (6831504) + upstream/main (271779b)` 無衝突。

## 2026-09-07：發布 v0.2.196

- 已取得使用者明確授權，刷新 `origin` 參照後確認兩個 push 都可安全以非 force 方式執行。
- `origin/main` 已推送至官方同步提交 `271779bef895c2443ebde4cdbe3e35bbf72be6de`。
- `origin/custom/main` 已推送同步後客製程式碼提交 `79dded326428e528949512e5a0bf645fdf4fa18b`。
- `Custom compatibility` 已成功完成：[Run 34088608570](https://github.com/Charlie-0926/locwarp/actions/runs/34088608570)；frontend 與 backend job 全部通過。GitHub 僅回報 Node.js 20 action deprecation annotation，未影響結果。
- 發布結果與 CI URL 已補入 `doc/upstream-sync/2026-09-07-v0.2.196.md`，並準備以文件提交同步至客製分支。

## 2026-08-16：上游同步 skill 版本一致性關卡

- 已更新 `C:\Users\charlielaptop\.codex\skills\locwarp-sync-upstream\SKILL.md`，要求每次合併官方更新時，以官方 release tag（例如 `v0.2.192`）去除前導 `v` 後的版本作為應用程式版本，並在驗證與提交前同步客製版本。
- 要求 `frontend/package.json`、`frontend/package-lock.json` 頂層 `version` 與 `packages[""]` 的 `version` 三處完全一致；流程使用 `npm version --no-git-tag-version --allow-same-version` 更新版本中繼資料且不建立 Git tag。
- 已要求官方 release tag 與 `upstream/main:frontend/package.json` 必須一致；若兩者不一致就停止同步並調查，不可默默選用其中之一。另不可僅為了配合應用程式版本而修改 `backend/main.py` 的 FastAPI schema 版本。
- 已將版本一致性加入同步報告、完成報告與發布前安全檢查。
- 已用 `quick_validate.py` 驗證 skill 結構（`Skill is valid!`），並以 `npm version 0.2.192 --no-git-tag-version --allow-same-version --dry-run` 驗證命令可執行；SHA-256 前後比對確認兩個正式版本檔均未改動。
- 已核對 `frontend/src/components/UpdateChecker.tsx`：GitHub release tag（例如 `v0.2.192`）會先移除 `v`，再與 `frontend/package.json` 的 `0.2.192` 比較；因此 skill 新增的 manifest 版本同步正是用來避免同步後仍誤報有新版。既有安裝檔若仍內含舊版本，仍須重新建置與安裝。
- 已實際驗證目前同步參照：tag `v0.2.192`、正規化版本 `0.2.192`、官方 manifest `0.2.192`，以及客製 package/lockfile 三處 `0.2.192` 全部一致；修正後 skill 再次通過 `quick_validate.py`。

## 2026-07-30：上游同步 preflight

- 已完整讀取 `locwarp-sync-upstream` skill、`doc/upstream-sync/README.md`、`doc/custom-feature-ledger.md`，以及 `scripts/rehearse-upstream.ps1`、`scripts/sync-upstream.ps1`、`scripts/check-extension-boundaries.ps1`、`scripts/verify.ps1`。
- repository 內未找到實體 `AGENTS.md`；本次依對話提供的 AGENTS 指示執行，每個小任務完成後更新 `doc` 進度文件。
- 初始檢查確認工作樹乾淨，且目前分支為 `custom/main`。
- 已確認 remote 契約正確：`upstream` 指向 `keezxc1223/locwarp`，`origin` 指向 `Charlie-0926/locwarp`。
- 已抓取官方 tags 與 `upstream/main`；官方從 `v0.2.190`（`c1a6c36`）前進到最新 tag `v0.2.192`（`aec015d`），其後另有 README commit `a1ebe20`。
- 官方新增 3 個 commits，重點為右鍵「移動到」長選單捲動、前後端相依套件大版本升級，以及中英文 README 更新；抓取後 `custom/main...upstream/main` 分歧為 16／3。
- 已建立本次同步報告：`doc/upstream-sync/2026-07-30-v0.2.192.md`。
- merge rehearsal 已執行；`README.md`、`README.en.md`、`backend/requirements.txt` 有內容衝突，其餘官方變更可自動合併。下一步在正式 `sync/upstream-v0.2.192` 分支依官方意圖與客製功能帳本解決。
- 正式同步已建立 `sync/upstream-v0.2.192`，並將本機 `main` 鏡像更新到官方 `a1ebe20`。
- README 衝突採官方「多點路徑 / Multi-point Route」命名，完整保留客製的到站等待、固定方向直線移動、pause／hot-apply 與精確終點行為。
- `backend/requirements.txt` 採官方 v0.2.192 的新版相依範圍，並將 `pymobiledevice3` 固定為官方目標版 `10.1.0`，保留客製打包的可重現性；衝突標記掃描與 `git diff --check` 均通過。
- 官方 v0.2.192 lockfile 與 manifest 不一致，首次 `npm ci` 偵測到缺少 `@emnapi/core`／`@emnapi/runtime` 及 `@emnapi/wasi-threads` 版本不符；已用 `npm install` 校正 lockfile，第二次乾淨 `npm ci` 成功。
- 已確認實際安裝 Electron 43.2.0、React／React DOM 19.2.8、TypeScript 7.0.2、Vite 8.1.5；npm audit 回報 18 個 high severity 項目，未在同步流程中執行可能導致 breaking changes 的 `npm audit fix --force`。
- 本機 Python 3.13 原安裝位置已不存在，既有 venv 無法啟動；依 sync skill，Python pytest／Mypy（包含 2-opt regression）改由推送後的 `Custom compatibility` GitHub Actions 強制覆蓋。
- `scripts/check-extension-boundaries.ps1` 已通過，確認官方更新未讓已抽離功能重新滲回核心，也未遺失必要 extension module。
- 客製能力 wiring audit 共 39 項檢查全部通過，涵蓋 Spiral、Jump dwell／hot apply、2-opt、multi-device 對齊／鏡像／leader handoff、單一執行個體、跨 waypoint 速度維持，以及 Pyright／Mypy／async 相容接線。
- 2-opt 實作與 regression test 已人工複核：固定起點、完整非重複 waypoint order、O(1) prefix-delta 候選成本、非對稱 matrix、`None` 不可達邊拒絕，以及對稱／非對稱 first-improvement oracle 覆蓋均仍存在。
- `scripts/verify.ps1` 全部通過：extension boundaries、Backend Pyright（0 errors／warnings）、Electron syntax、React 19 + TypeScript 7 型別檢查及 Vite 8 production build。僅有既存 dynamic-import／大型 chunk 警告。
- 整合 staged diff 已逐檔 review；最終 `git diff --cached --check`、衝突標記掃描均通過，`doc/coordinates.txt` 未被追蹤且仍由 `.gitignore` 明確忽略。
- 已在 `sync/upstream-v0.2.192` 建立雙親 merge commit `6211564`，父 commit 為客製 `bef82f0` 與官方 `a1ebe20`。
- 已將 `custom/main` 以 `--ff-only` 推進至 sync branch 最新 commit `9f45017`；未改寫歷史。
- fast-forward 後 rehearsal 已通過：`custom/main` `7efc5af` + `upstream/main` `a1ebe20` 無衝突。
- 已非 force push：`origin/main` 更新至官方鏡像 `a1ebe20`，`origin/custom/main` 更新至已驗證程式碼 commit `910652a`。
- `Custom compatibility` run `30529997877` 已成功；backend requirements 安裝、extension pytest（含 2-opt）、Mypy、Pyright，以及 frontend `npm ci`、TypeScript、production build 全部通過。
- CI URL：<https://github.com/Charlie-0926/locwarp/actions/runs/30529997877>
- 尚待實機確認：pymobiledevice3 10.1.0 的 USB／Wi-Fi tunnel 與兩台 iPhone 的 multi-device auto-sync、UI mirroring、state alignment、leader handoff；CI 不取代實機行為驗證。

## 2026-07-18：跳躍停留順序與移動秒數調整（已完成）

- 使用者已確認前一版固定方向 15 km/h／4 秒移動在單台與雙台實機均正常。
- 第一小段已完成：後端 request、runtime engine 與 hot-apply contract 新增 `jump_move_seconds`，預設 4 秒且最小值為 0；未傳新欄位的舊客戶端維持 4 秒相容行為。
- 第二小段已完成：multi-stop／route-loop 每站先快照 enabled、`n`、`m`，依序執行 idle wait 再建立 movement session；方向因此只會在等待結束後抽一次。
- ETA、pause countdown 與 dwell event elapsed 已統一為 `n+m`；idle 事件從 0 累計到 `n`，movement 事件從 `n` 累計到 `n+m`，完成事件速度歸零。
- 第三小段已完成：後端測試新增自訂 `m` 距離與「idle 先於 moving」斷言，並同步驗證預設 4 秒、pause／stop、閉環與非循環終點；jump extension 共 11 項通過。
- 第四小段已完成：前端新增 `locwarp.jump.move_seconds`（預設 4）及「直線移動時間」輸入；畫面順序為先等待、再啟用直線移動與設定 `m`。
- 單台／雙台 start request 與 hot apply 均會傳 enabled、`n`、`m`；摘要顯示「先等待 n 秒，再以 15 km/h 移動 m 秒，共 n+m 秒」。Frontend TypeScript 已通過。
- 第五小段已完成：README 中英文、功能帳本與評估文件已同步「先等 n、再走 m」及固定 15 km/h 語意。
- 最終自動驗證通過：backend 19 passed、extension boundaries 通過、Pyright 0 errors、Electron syntax／Frontend TypeScript／production build 全部通過；僅有既有 Vite CJS、混合 import 與大 chunk 警告。
- 最終 diff／空白檢查通過；未觸碰既有不相關的 `doc/2026-07-16-route-start-index-log-audit.md`。
- 實機驗收完成：使用者確認現行「先等待 `n`、再以 15 km/h 移動可調 `m` 秒」版本在單台與雙台裝置皆運作正常，可提交保存。
- 已建立功能 commit：`feat: add configurable post-jump linear movement`；僅收錄本功能的程式、測試與文件，不包含不相關的 7/16 稽核文件。

## 2026-07-18：點對點跳躍改為到站後固定方向直線移動

- 移除 jump mode 的跳躍前等待；舊 pre/post 設定會遷移並正規化成單一到站後額外等待 `n`。
- 每個一般停靠點到站後隨機選一次 bearing，以 15 km/h 直線移動 4 個有效秒（約 16.67 m），再於終點等待 `n` 秒；pause 凍結兩階段，hot apply 從下一站生效。
- 重構 multi-stop／route-loop post-dwell、ETA 與閉環 traversal；有限圈數精確停在 waypoint 0，非循環最後一點精確停在終點。
- 前端移除 pre-delay 與半徑 UI，新增舊 localStorage 遷移、`4+n` 說明、enabled+n hot apply 及 dwell 即時速度顯示。
- 新增 contract、幾何、時序、pause/stop、閉環與最後點測試；完整驗證結果記錄於 `doc/2026-07-18-jump-dwell-linear-movement-assessment.md`。

## 2026-07-16：增量 2-opt 與 sync skill 紀錄發布

- 已將 `custom/main` 推送至 `origin/custom/main`；第一輪遠端由 `87a946d` 更新至 `de8918e`，包含既有 `a297895`、增量 2-opt `06d74fa` 及 skill 完善紀錄 `de8918e`。私有 `doc/coordinates.txt` 未追蹤且未上傳。
- Push 後確認本機與遠端 SHA 一致。GitHub Actions 未產生 `Custom compatibility` run：workflow 檔僅存在 `custom/main`，repository 預設分支 `main` 未包含任何 workflow，因此 GitHub 未註冊該 workflow；依 thin-fork 契約未將客製 workflow 加入官方鏡像 `main`。

## 2026-07-16：`locwarp-sync-upstream` 對增量 2-opt 的適用性稽核

- 已完善個人 Codex skill `C:\Users\charlielaptop\.codex\skills\locwarp-sync-upstream\SKILL.md`：同步後須明確保留固定起點、完整且不重複的 waypoint 順序、O(1) 增量候選評估、非對稱 matrix 與不可達邊防護；相關變更時必跑 route optimizer regression test。
- Skill 新增私有資料安全規則：`doc/coordinates.txt` 等本機路線輸入不得加入 Git、CI fixture、skill resource 或同步報告，只能記錄彙總效能數據；更新後 `quick_validate.py` 回報 `Skill is valid!`，`agents/openai.yaml` 仍與 skill 用途一致。
- 增量 2-opt 提交前 review 無阻擋問題：1,040 組隨機非對稱 matrix 與舊版演算法順序完全一致；backend 9 項測試及完整 `scripts/verify.ps1`（extension boundaries、Pyright、Electron syntax、TypeScript、production build）均通過。
- 依 skill 規則唯讀檢查 `doc/upstream-sync/README.md`、客製功能帳本、同步／預演／驗證腳本及 GitHub compatibility workflow。
- 現行 skill 已能保護此次修改：feature ledger 已記錄增量 2-opt，extension boundary 要求 `two_opt.py` 存在，CI 會執行 `backend/tests/extensions`，因此對稱、非對稱、不可達邊與固定起點 regression tests 都會在同步後執行。
- skill 無必要立即修改；建議後續小幅強化第 7、9 步，明列 2-opt 必須維持增量成本、固定起點、非對稱／不可達邊行為，並明確執行 `backend/tests/extensions/test_route_optimizer.py`。私有 `doc/coordinates.txt` 應繼續只留本機，不加入 skill、CI 或同步報告。
- 已依 skill 安全規則完成本次 2-opt 與文件變更的 review，並準備以獨立功能 commit 保存，避免日後 upstream sync 混入未提交內容。

## 2026-07-16：400+ 點 2-opt／LKH-3 唯讀評估

- 私有 434 點資料最終比較：舊版 134.100 秒；最終版連跑 5 次中位數 1.386 秒，約快 96.7 倍、耗時降低 98.97%。兩版距離皆為 63,297.434 公尺，新版 5 次順序完全一致，且路徑合法、固定起點正確。
- `doc/coordinates.txt` 已加入 `.gitignore`，避免私有基準座標被誤 commit 或 push；測試與文件均不複製座標內容。
- 補上 duration matrix 含不可達 `None` 邊的防護與測試；backend 完整測試為 9 項通過。
- 最終靜態檢查通過：route optimizer 實作與測試的 Pyright 結果為 0 errors、0 warnings、0 informations；`git diff --check` 通過。
- 完成增量成本 2-opt：候選評估不再複製並重算完整路徑，改以邊界差額與反向內部邊前綴和做 O(1) 比較；只有接受改善時才實際反轉片段。此作法保留 first-improvement 行為，也支援非對稱 duration matrix。
- 新增對稱／非對稱 matrix 的舊版演算法 regression oracle 測試，固定與非固定起點皆須產生相同順序；route optimizer 測試共 4 項通過。
- 實際私有座標集 `doc/coordinates.txt`（434 點）改善前基準完成：haversine matrix 0.037 秒、nearest-neighbor 距離 75,489.419 公尺、舊版 2-opt 134.100 秒、改善後距離 63,297.434 公尺；結果包含全部 434 點且固定起點正確。基準只在本機執行，未輸出或上傳座標內容。
- 完成現行 route optimize 呼叫流程與 2-opt 複雜度分析；確認每個候選都複製並重算整條路徑，使完整掃描約為 O(n³)，是 400+ 點的主要 solver 瓶頸。
- 合成 Euclidean matrix 基準：50 點 0.018 秒、100 點 0.259 秒、200 點 5.967 秒；未直接執行可能長時間阻塞的 400 點測試。
- 確認超過 100 點時 OSRM table 會跳過，實際等待也可能包含 Valhalla matrix 與 haversine fallback，後續應先加入分段計時。
- 評估 LKH-3：解品質與規模能力較強，但需要 open-path/dummy-node 轉換、ATSP／整數成本處理、Windows binary 打包及 timeout/fallback；其研究／非商業授權亦與 LocWarp 的 MIT 商用授權不相容。
- 唯讀評估後已依使用者指示完成既有 2-opt 優化；實測已達到 400+ 點速度需求，暫時不需要導入外部 solver。完整內容見 `doc/2026-07-16-route-optimizer-lkh3-analysis.md`。

## 2026-07-15：WiFi tunnel TLS-PSK runtime 修正

- Updated `build-installer.bat` to prefer the project Python 3.13 `venv` and fall back to `py -3.13`, so future rebuilds reuse the verified dependency environment.
- Electron/NSIS packaging completed successfully. Final artifact: `frontend/release/LocWarp Setup 0.2.190.exe` (150,117,817 bytes, SHA-256 `2C3DBDFE0564773DE8159EE510C5742611331663414EE5A5DA80E5165617FA8B`).
- Final unpacked installer verification confirms `python313.dll=true` and `python311.dll=false`; the complete backend test suite passes (`6 passed`).
- Frontend TypeScript and Vite production build completed successfully; only the existing bundle-size/dynamic-import warnings remain.
- Promoted the verified Python 3.13 bundle to `dist-py/locwarp-backend`, which is the backend resource consumed by Electron packaging.
- Built a clean PyInstaller backend with Python 3.13.13 into `dist-py313`; the bundle contains `python313.dll` (and no `python311.dll`) plus the compiled `lzfse` extension.
- Smoke-tested the frozen `locwarp-backend.exe`: it started successfully, served `http://127.0.0.1:8777/` with `status: running`, and was then shut down cleanly.
- Installed the minimal Microsoft C++ Build Tools workload and successfully compiled `lzfse 0.4.2` for CPython 3.13; all backend/build dependencies are now installed in the project `venv`.
- Runtime tests pass (`2 passed`), and both the native TLS-PSK API and `pymobiledevice3.remote.tunnel_service` import successfully under Python 3.13.13.
- Installed and verified Python 3.13.13 (64-bit); `SSLContext.set_psk_client_callback` is available as required.
- Pinned `pymobiledevice3==9.30.1`, matching the previously packaged backend and preventing unreviewed tunnel API drift during rebuilds.
- Python 3.13 dependency installation is currently blocked only by `lzfse` requiring a local MSVC build on Windows; the minimal official build toolchain is the next setup step.
- 在 `backend/core/wifi_tunnel.py` 加入 Python 3.13 與 TLS-PSK 執行環境預檢；不相容的舊後端現在會立即回報明確原因，不再誤顯示為 tunnel timeout。
- 在 `backend/api/device.py` 將此錯誤映射至既有的前端錯誤碼 `python313_missing`。
- 在 `backend/locwarp-backend.spec` 加入同等的打包防呆，並將 `build-installer.bat` 改為明確解析及使用 `py -3.13`，避免再次誤用 Python 3.11。
- 新增 `backend/tests/test_wifi_tunnel_runtime.py`，接下來進行 Python 3.13 環境驗證與新版 Windows installer 打包。

## 2026-07-15：建立 LocWarp 官方更新同步 Skill

- 已在個人 Codex Skills 目錄建立 `locwarp-sync-upstream`，封裝 thin fork 的 upstream fetch、merge rehearsal、同步分支、衝突處理、客製功能稽核、驗證、文件更新、push 與 GitHub Actions 監看流程。
- Skill 強制維持 `main` 為官方鏡像、`custom/main` 為客製發布分支，禁止直接污染客製主分支或使用 force push。
- 已使用 Skill Creator 的 `quick_validate.py` 驗證，結果為 `Skill is valid!`。

## 2026-07-15：完成 thin fork 客製擴充邊界強化

- GitHub Actions 最終通過：extension pytest、全 backend Mypy、backend Pyright、frontend TypeScript 與 production build 全部成功。首次執行找到的 Windows `ctypes` 平台型別及 GPX loop variable narrowing 共 10 項錯誤已修正。
- 將 Jump Random Walk 的 backend dwell policy/schema/router 與 frontend API/control UI 移至客製 extension。
- 將 2-opt 演算法與 frontend adapter 移至 route optimizer extension，並加入單元測試。
- 將多裝置 backend coordinator 及 frontend runtime/fan-out/synchronize-start 移至 extension；同時修正 ETA tracker 鏡像寫入唯讀 property 的問題。
- 加入客製 location router、extension boundary check、GitHub Actions compatibility workflow 與三組 extension tests。
- 完整 `scripts/verify.ps1` 通過：Pyright 0 errors、Electron syntax、TypeScript 與 Vite production build 全部成功；僅既有 bundle 警告。
- 已 fetch 官方 upstream，最新版仍為 v0.2.190 (`c1a6c36`)；目前 `custom/main` 的 merge-tree rehearsal 通過，與官方版本無衝突，且已推送至 `Charlie-0926/locwarp`。

## 2026-07-15: 官方版本同步與客製模組化架構盤點
- 已找到並設定本方 fork `Charlie-0926/locwarp` 為 `origin`；目前 `origin/main` 與官方 `upstream/main` 同為 v0.2.190，本機 `custom/main` 含本次稽核文件後多 5 個尚未推送的客製／整合 commits。
- 完成 `doc/2026-07-15-custom-feature-merge-audit.md`：逐項確認 Spiral、Jump Random Walk、2-opt、多裝置同步／鏡像／接手、Pyright/Mypy 與 async 修正的程式路徑均未在合併中遺失。
- 重跑 `scripts/verify.ps1`：Pyright 0 errors、Electron 語法、TypeScript 與 Vite production build 全部通過，且無 conflict markers；Mypy 因本機沒有可用 Python interpreter 而無法在本輪重跑。
- 已實際將官方 v0.2.190 合併到客製版：同步分支 `sync/upstream-v0.2.190`，merge commit `705fbea`，並 fast-forward 回 `custom/main`；乾淨 `main` 持續對齊 `upstream/main`。
- 11 個衝突已解決並由 `rerere` 記錄；同時保留客製 Spiral／等待隨機漫步與官方 Flower／Wi-Fi dwell keepalive，正式 build、tsc、Electron 語法檢查通過，Pyright 0 errors。
- 新增 `scripts/rehearse-upstream.ps1`、`scripts/sync-upstream.ps1`、`scripts/verify.ps1` 與 `doc/upstream-sync/` 操作／同步紀錄，形成固定的試合併、正式同步、驗證與人工核准流程。
- 新增 `.gitattributes` 統一主要原始碼換行規則，降低 Windows CRLF 造成的無效 diff 與衝突。
- GitHub connector 未找到本方既有 locwarp fork，因此尚未設定 `origin` 或推送；需由維護者決定 repository owner 與公開／私人屬性。
- 已提交既有客製快照 `d18ba45`，後續架構調整不再與歷史客製差異混在同一 commit。
- 完成第一個實際 extension 遷移：backend 新增 `extensions` registry 並將 Spiral handler/schema 移入 `backend/extensions/custom/spiral/`；frontend 將 Spiral API adapter、descriptor 與設定面板移入 `frontend/src/extensions/custom/spiral/`。
- Spiral 在核心的接點已縮減為 handler registry lookup、API router import 與前端元件／呼叫 adapter；Pyright 0 errors、TypeScript `tsc --noEmit` 通過、Vite production build 通過（僅既有 chunk/dynamic import 警告）。
- 已恢復原本空白的 `.git`：下載官方完整歷史與 tags，以官方 v0.2.177 (`53042c6`) 作為客製共同基底。
- 已建立 `custom/main` 保存目前客製工作樹；本機 `main` 已追蹤乾淨的 `upstream/main` v0.2.190，並啟用 `git rerere` 與 `zdiff3` 衝突格式。
- 新增 `doc/custom-feature-ledger.md`，將功能分類為 local-only、upstream-candidate、available-upstream 與 integration。
- 檢查官方 `keezxc1223/locwarp` 近期版本與 commit；官方最新為 v0.2.190，v0.2.189 已正式包含「套用速度跨路徑點維持、停靠期間可套用」修正。
- 盤點本機客製功能分布，確認 Spiral、等待期間隨機漫步等功能會修改 `simulation_engine.py`、`App.tsx`、`useSimulation.ts`、`ControlPanel.tsx` 等上游高衝突熱點。
- 確認本機 `frontend/package.json` 仍標示 v0.2.177；目前 `.git` 目錄為空且 Git 無法辨識 repository，尚不能直接設定 upstream 或執行安全合併。
- 完成 `doc/2026-07-15-upstream-modularization-plan.md`：建議採 thin fork、乾淨 upstream mirror、`custom/main`、backend/frontend extension registry、功能帳本及 CI 試合併流程。
- 本次只完成架構分析與文件，未重構程式；下一步應先建立乾淨官方 clone、確認共同基底並重建可追溯的客製 commits。

## 2026-07-15: 診斷 build-installer.bat 無法執行
- 重現執行 `build-installer.bat`：流程停在 `[1/3] Build backend`，錯誤為 `'python' is not recognized as an internal or external command`。
- 環境檢查：`python.exe` 不在 PATH，`py --version` 也回報 `No installed Python found!`；Node.js `v24.15.0` 與 npm `11.12.1` 可用。
- 根因是目前電腦未安裝／未提供 Python 3.13，尚未進入 Vite 或 electron-builder 階段；本次只完成診斷，未修改打包設定。
- 2026-07-15 再次重試仍停在相同位置；`where python` 找不到執行檔，常見 Python 3.12／3.13 安裝路徑也未發現。
- 使用使用者提供的 Python 3.11.4 重新執行後，PyInstaller backend 與 Vite frontend 均成功；最後 electron-builder 在解壓 `winCodeSign-2.6.0.7z` 時因無法建立 `libcrypto.dylib`／`libssl.dylib` symbolic link 而失敗。另有 `frontend/build/build/icon.ico` 不存在的非致命路徑警告。

## 2026-07-15: 修正巡迴／多點路徑套用速度後於路段切換失效
- `backend/core/simulation_engine.py`：套用速度時立即保存新 profile；即使正在停靠等待、路段切換或等待下一段路由，也不再誤判為沒有進行中的路線，下一段會套用新速度。
- `backend/core/route_loop.py`：未套用新速度時維持原本每圈一次的速度選擇；一旦套用新速度，後續每個路段與每一圈都改用 engine 的最新 profile，不會被啟動時的舊設定覆蓋。
- 驗證：Pyright `0 errors, 0 warnings, 0 informations`；`npx.cmd tsc --noEmit` 通過；`node --check frontend/electron/main.js` 通過；`npm.cmd run build` 通過（僅有既有 dynamic import／chunk size 警告）。
- 尚未執行真機速度回歸測試；目前環境沒有可直接啟動 iOS backend 的 Python runtime／裝置連線。

## 2026-07-15: 防止 LocWarp 重複啟動造成無效工作
- 新增 `backend/instance_lock.py`：Windows 使用 named mutex，POSIX 開發環境使用 advisory file lock；模組放在 backend 根目錄，避免啟動器載入 `core/__init__.py` 的裝置依賴。
- `start.py`／`LocWarp.bat` 啟動前取得 `LocWarp.DevLauncher` 鎖；若已有啟動器執行，直接提示並取消第二次啟動，避免清理 8777/5173 時誤殺第一個實例。
- `backend/main.py` 使用 `LocWarp.Backend` 鎖，直接重複執行 backend 時會記錄錯誤並退出。
- `frontend/electron/main.js` 使用 Electron `requestSingleInstanceLock()`；第二次開啟會切回既有 LocWarp 視窗，不會再建立第二個 renderer/backend。
- 修正啟動順序：鎖模組移至 `backend/instance_lock.py`，`start.py` 不再因匯入 `core/__init__.py` 而提前載入裝置依賴。
- 驗證：`node --check frontend/electron/main.js` 通過；`npx.cmd tsc --noEmit` 通過；`npm.cmd run build` 通過（僅有既有 chunk size／dynamic import 警告）。
- Python 語法與鎖競爭測試尚未能在目前環境執行，因該 shell 沒有可用的 Python runtime（`py` 也回報未安裝 Python）；程式碼已依 Python 3.13／Windows named mutex API 寫法檢視。

## 2026-06-25: 分析本機與最新官方遠端專案 (v0.2.186) 的功能差異
- **分析與對比**：
  - 下載官方最新 v0.2.186 專案原始碼，與本機自訂版本（基於 v0.2.177 加自訂修改）進行全面的檔案與程式碼比對。
  - 整理出官方最新版新增之重要功能（「種花模式 (Flower Mode)」、「書籤 GPX 匯入與多維匯出/壓縮檔下載」、「書籤地圖 Supercluster 效能優化與視窗裁剪渲染」、「NumberField 輸入框防抖與延遲更新」等）。
  - 明確列出本機已實現但官方遠端尚未擁有的客製化功能（「中心繞圈 (Spiral Mode)」、「點對點跳躍等待期間隨機漫步 (Jump Random Walk)」、「2-opt 最佳路徑演算法」、「多裝置自動同步 UI 狀態鏡像及狀態對齊」以及「全專案 Pyright/Mypy 靜態型別與非同步語法修復」等）。

## 2026-06-13: 徹底修復 IDE 與 Pyright 靜態分析之語法與型別錯誤
- **`backend/api/device.py`**:
  - 將全域變數 `MAX_DEVICES` 的定義移到檔案頂端，消除了 `possibly unbound variable` 警告。
  - 對 `CoreDeviceTunnelProxy.close()` 進行非同步檢查 `inspect.isawaitable` 並正確使用 `await`，解決了 `reportUnusedCoroutine` 錯誤。
  - 引入 `typing.cast` 對 `amfi_lockdown` 進行 `cast(Any, ...)`，解決 `reportArgumentType` 類型不匹配錯誤。
- **`backend/services/location_service.py`**:
  - 將 `_reset_service` 函式修改為 `async def`，並引入 `inspect.isawaitable` 判斷對 `self._service.close()` 返回的協程進行 `await`。
  - 將其在 `set` 與 `clear` 內部的呼叫改為 `await self._reset_service()`。這消除了協程未被 `await` 的 `reportUnusedCoroutine` 嚴重 IDE 警告/錯誤，也避免了潛在的資源洩漏。
- **`backend/core/device_manager.py`**:
  - 引入 `typing.cast` 將 `conn.lockdown` 轉換為 `Any`，傳給 `MobileImageMounterService`、`DvtProvider` 與 `mount_fn`，消除因為 `conn.lockdown` 原本宣告為 `object` 導致的所有 `reportArgumentType` 型別錯誤。
  - 對 `conn.tunnel_proxy.close()` 進行 Awaitable 判斷並 `await`，解決 `reportUnusedCoroutine` 錯誤。
- **`backend/core/simulation_engine.py`**:
  - 在 `_move_along_route` 迴圈外部提前初始化 `wp_seg_idx` 與 `wp_hit_ptr` 變數，解決了在迴圈提前 break 時變數 `possibly unbound variable` 的編譯期 IDE 警告。
- **驗證**：
  - 執行 `npx.cmd --yes pyright backend/` 回報 **0 errors, 0 warnings, 0 informations**，所有 IDE 錯誤與底線皆已完全消除。
  - 執行 `python check_project.py` 回報 `[PASS]`，專案合併任務順利達成。

## 2026-06-13: 完成與源專案 (v0.2.177) 合併與靜態分析型別修復
- 合併：成功完成了後端與前端共 12 個衝突檔案與其餘非衝突檔案的合併，全面保留了「中心繞圈 (Spiral Mode)」、「跳躍等待隨機漫步 (Jump Random Walk)」、「雙裝置同步強化」與「O(N) 提早跳出最佳化」等客製化功能，並成功融入官方 v0.2.177 最新功能（包含：本機/WiFi keep-alive、版面導航列優化、跳躍前/後延遲設定、路徑點摺疊 UI 等）。
- 靜態分析與 IDE 錯誤修復：
  - 在後端所有涉及未提供型別存根（Type Stubs）的第三方庫（`pymobiledevice3` 與 `psutil`）匯入處，全面且精準地加上了 `# type: ignore[import-untyped]` 與 `# type: ignore[import-not-found, import-untyped]` 標記。
  - 受影響並修復的檔案包含：`location_service.py`、`wifi_tunnel.py`、`random_walk.py`、`device_manager.py`、`phone_control.py`、`device.py` 與 `main.py`。
  - 這確保了即使**不使用** `--ignore-missing-imports` 引數直接執行 `mypy`，或者在使用 VS Code/PyCharm 等 IDE 開啟專案時，**所有檔案均不會顯示任何紅色底線/型別錯誤**。
  - 修復 `backend/services/recent.py` 座標 float 轉型可能為 None 的型別檢查錯誤。
  - 修復 `backend/core/wifi_tunnel.py` 中 `self.task` 在停止時的 None 安全檢查錯誤。
  - 修復 `backend/services/gpx_service.py` 迴圈變數 (pt) 重複定義之型別衝突。
  - 修復 `backend/services/coord_format.py` 在 DM 與 DMS 模式變數重複賦值時的型別不一致。
  - 修復 `backend/core/multi_stop.py`、`backend/core/spiral_walk.py`、`backend/core/random_walk.py`、`backend/core/joystick.py` 與 `backend/core/route_loop.py` 中 `SpeedProfile` TypedDict 覆寫與 `dict` 轉型產生的型別檢查錯誤。
  - 修復 `backend/services/geo_extras.py` 與 `backend/services/geocoding.py` 中 httpx params 的型別定義。
  - 修復 `backend/core/device_manager.py` 的 DvtLocationService 覆寫、tunnel_context 與 RSD None 檢查。
  - 修復 `backend/api/phone_control.py` 呼叫 `subprocess.run` 時解包 params 物件導致的多載比對失敗。
  - 修復 `backend/main.py` 的 basicConfig 內部 `_handlers` 型別標記。
- 驗證：
  - 執行 `python check_braces.py` 驗證所有關鍵前端 TypeScript/TSX 檔案無括號不對稱。
  - 執行 `python check_mypy.py` 確認 `mypy` 即使不加任何忽略參數也回報 `Success: no issues found in 41 source files`，無任何型別與匯入問題。
  - 執行 `python check_project.py`（後端 Mypy 與前端 `tsc --noEmit`），兩端均回報 `[PASS]`。
  - 於 `frontend` 目錄執行 `npm run build` 成功建置生產環境檔案，無任何打包與編譯錯誤。
- 清理：已安全刪除 `.merge_tmp` 臨時目錄，保持工作區乾淨。

## 2026-06-13: 規劃與源專案 (v0.2.177) 合併計畫
- 分析：下載了官方 v0.2.177 與 v0.2.157 釋出版，並與本機自訂版本進行了全面的三向檔案比對 (3-way diff)。
- 規劃：整理出無衝突的覆蓋檔案清單，以及 12 個存在重疊變更的衝突檔案。針對這 12 個衝突檔案，逐一規劃了合併邏輯，以完整保留您的「中心繞圈 (Spiral Mode)」、「跳躍等待隨機漫步 (Jump Random Walk)」、「雙裝置同步強化」等功能，並同步引入官方新版功能 (如：本機/WiFi keep-alive、版面導航列優化、跳躍前/後延遲設定、路徑點摺疊 UI 等)。已建立完整的實作計畫 `implementation_plan.md`。

## 2026-06-06: 修復路線巡邏跳躍隨機移動錯誤與新增全專案檢查腳本
- 修復：解決在「路線巡邏」中開啟「點對點跳躍」並啟用隨機移動時，會發生 `SimulationEngine.start_loop() got an unexpected keyword argument 'jump_random_walk'` 的 TypeError 錯誤。已在 `backend/core/simulation_engine.py` 的 `start_loop` 方法中加入對應的參數 (`jump_random_walk` 和 `jump_random_walk_radius`) 並正確傳遞給底層處理器。
- 新增：建立 `check_project.py` 全專案靜態分析檢查腳本。該腳本可一鍵執行後端 (Python/mypy) 與前端 (TypeScript/tsc) 的型別和語法檢查，確保未來每次功能更新時，可快速發現未對齊的函式簽名或型別錯誤，避免同樣的參數缺少錯誤再次發生。
- 診斷：完成對「路線巡邏 (Multi-Stop)」的 Internal Server Error 深度檢查。經全方位追蹤後端日誌及原始碼，已確認 Pydantic 驗證 (`MultiStopRequest`) 與底層參數 (`SimulationEngine.multi_stop`, `MultiStopNavigator.start`) 均已完美對齊，且日誌中並無任何 500 錯誤或未處理的例外。確認該模組的代碼健康狀態良好。

## 2026-06-05: 多點導航與繞圈模式跳躍隨機移動修復
- 修復：解決在「點對點跳躍加等待期間隨機移動」時，狀態列的剩餘距離及時間不顯示的問題。透過在隨機漫步等待期間動態計算並頻繁發送 `position_update` 事件 (包含準確的 `eta_seconds`)，使前端介面能正確繪製並即時更新進度條與預計到達時間。
- 修復：解決在「點對點跳躍加等待期間隨機移動」時，按下暫停卻無法暫停，路徑仍會持續進行的問題。在 `_dwell` (等待邏輯) 以及換點的迴圈中加入嚴謹的 `_pause_event.wait()` 檢查，確保使用者按下暫停時，後端倒數計時與路徑都會被凍結，直到解除暫停。

## 2026-06-02: 最佳路線演算法優化 (2-opt) 與 跳躍隨機移動 (Jump Random Walk)
- 最佳路線計算優化 (2-opt)：
    - 後端 (`backend/services/geo_extras.py`, `backend/api/geocode.py`)：為解決「最佳順序」計算在超過 8 個點位時因原有的窮舉法過於耗時而回退到照原順序，導致相鄰點位路線重疊的問題。實作了效能極佳的 `2-opt` 區域搜尋演算法，在 N > 8 時自動套用，大幅優化了長路線的排序品質，實測 10 個點位的計算耗時幾乎為 0 秒。
- 點對點跳躍 (Jump Mode) 支援隨機微移：
    - 後端 (`backend/core/route_loop.py`, `backend/core/multi_stop.py`)：在跳躍模式中加入了隨機漫步 (`jump_random_walk`) 的能力。當每次跳躍抵達座標點時，引擎不會在原地傻等，而會在用戶定義的範圍半徑 (`jump_random_walk_radius`) 內持續進行隨機的座標點平移，增加遊戲內的擬真度。
    - 後端 (`backend/core/simulation_engine.py`, `backend/api/location.py`)：開放即時套用介面 (Hot-swapping)。使用者能夠在跳躍路線執行途中隨時開關隨機移動或調整半徑，且立即在下一個跳躍週期的等待時間內生效。
    - 前端 (`frontend/src/components/ControlPanel.tsx`, `frontend/src/hooks/useSimulation.ts`)：在控制面板的跳躍模式區塊中，加入了「座標範圍隨機移動」的開關及「漫步半徑 (m)」的輸入框。此外，當處於執行狀態時，若使用者改變了隨機漫步的設定，會出現「套用」按鈕以觸發即時生效功能。
- 驗證與修復：完成了嚴謹的 TypeScript 編譯驗證及 Python 後端腳本功能測試，確保演算法精準且不會因 API 參數的加入而影響舊有的架構。

## 2026-05-28: Dual-Device Auto-Sync 修復 (多裝置自動同步)
- 後端 (`main.py`)：修復了雙裝置模式下，第二台裝置接入時無法跟隨的問題。
    - **擴充動態模式支援**：將 `SimulationState.SPIRAL` 加入 `dynamic` 白名單，現在即使在中心繞圈模式下插上第二台手機，系統也能正常啟動跟隨機制。
    - **支援暫停狀態接入**：新增了對主裝置處於 `PAUSED` 狀態的判斷，會自動抓取 `_paused_from` 來決定是否為動態模式，確保在暫停時插上的新手機，按下繼續後能正常跟著走。
    - **完善 UI 狀態映射 (State Mirroring)**：原本的 `_follow_primary_positions` 是「無聲推播」，不會發送任何事件給前端。現在已實作完整的狀態同步：
        - 接入當下：立即推送 `state_change` 與 `route_path`，讓第二台裝置在介面上也能畫出相同的路徑。
        - 輪詢推播 (0.5s)：除更新實體 GPS 外，同步發送 `position_update` WebSocket 事件，讓第二台裝置的地圖大頭針能跟著移動。
        - 狀態對齊：同步複製主裝置的 `eta_tracker` 屬性（包含預計到達時間、剩餘距離、進度），以及 `distance_traveled`。當主裝置暫停或繼續時，第二台裝置也會即時同步變更狀態。
- 驗證：完成 Python 語法驗證並進行了非同步邏輯的覆核，確保修正涵蓋了 `backend/main.py` 的 WebSocket 與屬性綁定操作，消除前台卡頓的假死現象。

---

## 2026-07-15: backend.log tunnel 建立失敗初步診斷

- 已讀取 `C:\Users\charlielaptop\.locwarp\logs\backend.log`（約 979 KB，最後寫入時間 15:50:54）。
- 15:45–15:48 的 USB tunnel 失敗皆落在 `pymobiledevice3.exceptions.PasswordRequiredError: ('PasswordProtected', ...)`；log 中共出現 113 次，表示裝置當下仍受密碼鎖定/未完成解鎖，Lockdown 不允許 `StartService`。
- 15:41–15:47 另有 Wi‑Fi RemotePairing `IncompleteReadError('0 bytes read on a total of 9 expected bytes')`，屬於 Wi‑Fi tunnel 候選連線被裝置端關閉或未完成握手，並非 USB tunnel 的主要例外。
- 15:48:33 重試後成功：15:48:34 `Tunnel established`、`RSD connected`、`Connected ... via USB`；之後 15:48:52 起 DVT location 與 multi-stop 更新正常。
- 同時發現 Personalized DDI 未掛載警告；這會影響需要 DDI 的功能，但不是本次 tunnel 建立失敗的直接原因。
- 原始碼對照確認 `backend/core/device_manager.py:303-334` 的 `CoreDeviceTunnelProxy.create()` 會在 `StartService` 階段拋出上述例外；目前實作將所有例外統一改寫成「請以系統管理員身份執行」，因此這個提示不能直接當作根因。
- 同一個裝置、同一個 backend 在 15:48:33–15:48:34 成功建立 USB tunnel，隨後 RSD、DVT 與 multi-stop 均正常；這排除了「固定缺少管理員權限」作為本次主要原因。
- Wi‑Fi 路徑 `backend/core/wifi_tunnel.py:41-45` 在 RemotePairing handshake 階段收到 `IncompleteReadError`；現有 log 足以確認握手被對端中斷，但不足以單獨判定是舊配對記錄、錯誤 port 或 iPhone 當時狀態。

## 2026-07-15: 修正雙裝置情境下的 Wi‑Fi tunnel 診斷

- 依雙裝置情境重新分流後，Wi‑Fi 目標是 UDID 結尾 `001C` 的裝置：它有 `remote_...001C.plist` 配對記錄；另一台 `00008101-...001E` 在 15:42:54 消失後，`001C` 仍於 15:43–15:47 單獨重試並失敗，因此鎖定裝置不是 Wi‑Fi tunnel 的根因。
- Wi‑Fi 的直接失敗點是 `pymobiledevice3` 的 RemotePairing `pair_verify`：`52009`/`62078` 連線後在等待 9-byte handshake magic 時收到 `IncompleteReadError (0 bytes)`；`49152`/`49157` 則 8 秒逾時。
- 15:43:29 起 mDNS/Bonjour 為空，程式改用 smart scan；但 `backend/api/device.py:300-365` 的 fallback 只驗證 TCP port 可連線，沒有驗證它是否真的是 RemotePairing protocol。這可解釋為何掃到多個 port 後仍全部無法完成握手。
- 本機 `remote_00008130-001C2DCE0243001C.plist` 最後修改時間為 2026-07-06；結合 handshake EOF，過期/失效 RemotePairing 記錄也是高度可疑因素。建議下一步以 USB 對該指定 UDID 執行 re-pair，並讓 mDNS 或 protocol-aware port discovery 找到正確 endpoint。
- 雙裝置額外風險：`backend/api/device.py:115-159` 的 `/wifi/repair` 沒有 UDID 參數，只取 `list_devices()` 回傳的第一台 USB 裝置；目前前端 `wifiRepair()` 也不傳 UDID。因此使用 UI 重新配對時可能修到另一台裝置，後續應改成指定 Wi‑Fi 目標 UDID（`...001C`）再進行修復。

## 2026-07-15: 單一裝置 Wi‑Fi tunnel timeout 根因確認

- 新一輪單裝置測試在 16:04:23 使用 `192.168.50.11:49152` 時已成功完成 `RemotePairing connected (identifier=...001C)`；因此 iPhone 可達、同網段與 RemotePairing 配對均已通過。
- 隨後在 `pymobiledevice3.remote.tunnel_service.start_tcp_tunnel()` 建立 TLS‑PSK 時於第 641 行拋出 `TypeError: 'NoneType' object is not callable`，具體是 `SSLPSKContext(ssl.PROTOCOL_TLSv1_2)`；UI 顯示的「Tunnel 啟動逾時」只是後續 fallback/timeout 的包裝訊息。
- 目前執行中的 `locwarp-backend` 對應工作區 `dist-py/locwarp-backend`，其中包含 `python311.dll`；而 `pymobiledevice3` 的 tunnel code 在 Python <3.13 分支依賴 `sslpsk_pmd3.SSLPSKContext`。該 import 失敗後被套件改成 `None`，造成 TLS tunnel 無法建立。
- 專案建置文件雖標示 Python 3.13，但 `build-installer.bat` 使用未限定版本的 `python`；現有 dist/build 產物是 Python 3.11。優先修正為以 Python 3.13 建置並重新打包，避免走 `SSLPSKContext` fallback；若仍支援 Python 3.11，則需另行修正/明確打包 `sslpsk_pmd3` 及其 OpenSSL runtime。

## 2026-07-15: Wi‑Fi TLS‑PSK 修正與重新打包（進行中）

- 已確認工作樹除本輪 `doc/progress.md` 外乾淨，修改基線位於 `custom/main`。
- Node.js `v24.15.0`、npm `11.12.1`、frontend dependencies 與 electron-builder 均已就緒。
- 系統目前找不到可用的 Python 3.13；`py` launcher 存在但回報沒有已安裝 Python，工作區也沒有 `venv`。因此需先完成建置防呆，再安裝 Python 3.13 才能產出正確 backend EXE。
- 現有 `dist-py/locwarp-backend` 明確包含 `python311.dll`，證實舊 installer 的 backend 是以 Python 3.11 打包。

## 2026-05-27: Spiral Mode (中心繞圈)
- 後端：新增 `SpiralRequest`、`SimulationState.SPIRAL`，實作阿基米德螺旋線邏輯 (`SpiralWalkHandler`)，新增 API `/api/location/spiral`，並將其整合進 `SimulationEngine` 中。
- 前端：於 `i18n` 新增中心繞圈相關字串；於 `services/api.ts` 介接 API `startSpiral`；於 `useSimulation.ts` 擴充 `SimMode.Spiral` 及對應的 fan-out 函式；於 `ControlPanel.tsx` 實作選單及「繞圈半徑 (m)」、「線距 (m)」的輸入框；於 `App.tsx` 加入 `spiralRadius` 與 `spiralSpacing` 的全域狀態與資料傳遞。
- 修復：解決後端 `simulation_engine.py` 初始化屬性覆蓋導致的方法呼叫錯誤，以及確保 TypeScript 檔案語法和型別引用正確無誤。
- 優化：在前端地圖介面上實作了「繞圈半徑」的視覺化預覽功能，選取繞圈模式時會顯示預期最大半徑的藍色虛線圓圈，讓使用者能直觀判斷範圍大小。
- 修復：前端 ETA 面板與狀態列遺漏了 `"spiral"` 狀態的註冊，導致開始繞圈後無法顯示預期到達時間、剩餘距離與底部狀態，現已補齊。
- 修復：後端 `spiral_walk.py` 處理繞圈路線時，強制改用「直線移動 (straight line)」。原本因為預設未開啟直線模式，導致系統將上萬個僅相距 10 公尺的螺旋點位送進 OSRM 道路導航引擎，造成龐大 API 請求擁塞與進度卡死。
- 修復 (重大)：後端 `simulation_engine.py` 在比對使用者節點與路徑點的進度計算中，存在 $O(N^2)$ 的效能瓶頸。當輸入點位高達 11,731 個時，會觸發超過 6,800 萬次的距離計算，導致引擎陷入死結無法推播位置更新。現已加入「距離小於 1 公尺提早跳出 (early exit)」的最佳化邏輯，解決了卡住不移動的狀況。
- 優化：前端 `ControlPanel.tsx` 現在會在選取「中心繞圈」時，自動隱藏「沿著道路移動」選項與「導航引擎」下拉選單。
- 修復：解決了在繞圈途中按下停止，並立刻開始新繞圈時，前端介面會丟失路徑與 ETA 但背景仍在移動的 Asyncio 競態條件 (Race Condition) 漏洞。現已確保 `_run_handler` 的 `finally` 區塊不會錯誤重置新任務的狀態。
