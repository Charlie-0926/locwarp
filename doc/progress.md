# 專案進度

## 2026-07-15: 官方版本同步與客製模組化架構盤點
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
