# 點對點跳躍到站直線移動評估與實作紀錄

## 討論後定案

這份計畫已依實機測試後的第二輪需求更新。目前定案的產品語意如下：

- 移除「跳躍前等待」，所有等待都發生在跳躍到站之後。
- 每次抵達路徑點後先原地等待使用者設定的 `n` 秒；等待結束時隨機選一次方向，同一次 movement session 的 bearing 固定。
- 以固定 15 km/h 直線移動使用者設定的 `m` 個有效秒；`m` 預設 4 秒且可設為 0。
- 每個一般停靠點的到站後總時間是 `n + m` 秒；關閉移動時只等待 `n` 秒。
- 暫停時間不算入等待 `n` 秒或移動 `m` 秒；恢復後從原階段與進度繼續。
- 移動完成後停在約 `4.1667×m` 公尺外，不瞬移回路徑點；下一站仍由點對點 teleport 抵達。
- hot apply 在下一次到站開始時整批套用，避免當次只走一半或等待時間突然改變。

固定參數：

| 項目 | 值 |
| --- | ---: |
| 速度 | 15 km/h = 4.1667 m/s |
| 移動時間 | 使用者設定 `m` 秒，預設 4 秒 |
| 總位移 | 約 `4.1667×m` 公尺 |
| 建議更新週期 | 0.5 秒 |
| 每 tick 位移 | 約 2.08 m |
| 到站後總時間 | 開啟移動時 `n+m` 秒；關閉移動時 `n` 秒 |

## 單一停靠點的執行順序

1. 立即 teleport 到目標路徑點，不再執行 pre-delay。
2. 更新 `segment_index`、`waypoint_progress`、`stop_reached`，先讓 UI 確認已到站。
3. 在到站座標原地等待 `n` 個「未暫停」的有效秒，同時維持現有 Wi-Fi tunnel keepalive。
4. 若「等待後直線移動」已開啟且 `m>0`，等待完成後隨機產生一個 0–360° bearing。
5. 以 monotonic clock 累計 `m` 個「未暫停」的有效秒，每 0.5 秒從原始到站座標計算累積距離並推送新座標。
6. 移動事件回報 `speed_mps=4.1667` 與固定 bearing；第 `m` 秒完成後回報 `speed_mps=0`。
7. 移動完成後，直接 teleport 到下一個路徑點。

座標必須用「到站起點 + bearing + 累積有效秒數 × 速度」計算，不能以上一次推送位置逐步相加；這可避免 I/O 延遲、排程誤差與浮點累積使速度或方向漂移。幾何可重用 `RouteInterpolator.move_point()`。

## 舊設定遷移

目前使用者有 `jump_pre_delay` 與 `jump_post_delay` 兩個值。既然所有等待都要移到到站後，建議新欄位定義為：

```text
new_extra_wait_n = old_pre_delay + old_post_delay
```

結果：

- 未開啟到站後移動：每站仍等待舊 pre + 舊 post 的總秒數，只是全部移到到站後。
- 開啟到站後移動：每站總時間變成 `m + old pre + old post`。
- 目前預設是 pre=2、post=4，因此新使用者的 `n` 預設為 6；`m` 預設為 4，開啟移動後每站預設共 10 秒。

前端使用新的 localStorage key，例如 `locwarp.jump.extra_wait`。第一次讀不到新 key 時，讀取舊 pre/post、相加後寫入新 key；之後只使用新 key。舊 key 不必主動刪除，方便版本回退。

API 建議接受一版舊 contract：

- 新 client 傳 `jump_dwell_motion` 與 `jump_extra_wait`。
- 舊 client 若只傳 `jump_random_walk`、`jump_pre_delay`、`jump_post_delay`，後端正規化為新欄位，並忽略舊 radius。
- 新欄位存在時以新欄位為準，避免新舊值重複相加。

## 特殊路徑語意

### 非循環多點路徑的最後一點

建議維持現況：最後一點只 teleport 到精確座標後完成，不執行 `n` 秒等待或 `m` 秒移動。否則任務完成位置會偏離使用者指定的最後路徑點約 `4.1667×m` 公尺。

這會形成一個明確例外：所有「後面還有下一跳」的停靠點使用 `n+m`，單趟最後點不使用 post-dwell。UI tooltip 與 README 必須說明。

### 閉環回第一點

移除 pre-delay 後，不能只是把既有 pre-delay 設成 0。現有 `route_loop.py` 在一圈結束時會 teleport 回 waypoint 0，下一圈的 for-loop 又會處理 waypoint 0；直接改參數會造成重複到站事件與重複 teleport。

建議重新整理閉環狀態：

- 抵達 waypoint 0 時先發出 `lap_complete`，代表上一圈已閉合。
- 若已達圈數上限，在 waypoint 0 精確座標停止，不再執行 `n+m` post-dwell，確保有限圈數的結束點正確。
- 若還要繼續下一圈，waypoint 0 的 `n+m` 視為下一圈的第一個 post-dwell；不得再次 teleport 或重複發出到站事件。

### 多裝置

目前每個 engine 都自行取 random。若延續現況，兩台裝置在同一站會選不同方向；這不影響路徑狀態同步，但座標不會重疊。

若未來要求兩台裝置方向一致，需由共用 seed 或每站 bearing 驅動所有 engine。這不是本次必要範圍，除非產品要求群組裝置重疊移動。

## 改動計畫

### 第一階段：建立新 domain contract

- 新增語意清楚的 runtime 欄位，例如 `jump_dwell_motion`、`jump_extra_wait`。
- 固定速度、時間與 tick interval 放在 custom extension 常數，不開放 UI 修改。
- 保留舊 request 欄位一版作正規化相容，不讓舊前端或外部 API 立即 422。
- hot-apply endpoint 同時套用 enabled 與 `n`，並明定從下一次到站生效。

涉及：

- `backend/models/schemas.py`
- `backend/core/simulation_engine.py`
- `backend/api/location.py`
- `backend/extensions/custom/jump_random_walk/schema.py`
- `backend/extensions/custom/location_router.py`

### 第二階段：實作固定方向 movement session

- 在 custom extension 內建立單次 dwell session，保存起點、bearing、有效 elapsed 與完成狀態。
- 到站時只抽一次 bearing。
- 使用 `RouteInterpolator.move_point()` 計算累積位置。
- 不加入 GPS jitter，確保真正固定方向。
- 位置推送加入與 `_move_along_route()` 同等級的有限重試與 DeviceLostError 處理。

涉及：

- `backend/extensions/custom/jump_random_walk/policy.py`（可先保留目錄名稱以降低 thin-fork 搬檔衝突）
- `backend/extensions/custom/jump_random_walk/__init__.py`
- `backend/tests/extensions/test_jump_random_walk.py`

### 第三階段：把 jump wait 改成 post-dwell 狀態機

- 移除所有 pre-delay 呼叫。
- 將 `jump_wait()` 拆成「原地等待 n 秒」與「移動 m 秒」兩階段，並固定依此順序執行。
- pause/stop 必須能立即喚醒 tick wait，不能沿用現況「pause 後仍可能多走一個 slice」的行為。
- 使用 monotonic deadline 扣除 `_set_position()` 與 event emit 耗時，避免實際速度低於 15 km/h。
- movement 完成後 speed 歸零，原地等待期間持續 keepalive。

涉及：

- `backend/core/multi_stop.py`
- `backend/core/route_loop.py`

### 第四階段：整理 traversal、ETA 與事件

- 每個一般停靠點的 dwell 公式改為 `motion_enabled ? n+m : n`，所有剩餘時間與 ETA 使用同一個 helper，避免多處各算一套。
- 移除 ETA 中的 `pre_delay + post_delay`。
- 修正閉環 waypoint 0，避免回起點後又重複 teleport。
- 明確保留非循環最後點不執行 post-dwell。
- jump route 的全域 distance 仍維持 0，避免 16.67 m dwell 軌跡污染點對點路徑距離；事件仍回報 speed 與 bearing。
- `pause_countdown` 若繼續沿用，duration 應為完整 `n+m`，並增加 phase 讓 UI 可區分 idle／moving。

### 第五階段：更新前端設定與顯示

- 移除「跳躍前」輸入。
- 等待欄位命名為「到站後先等待」，值為 `n`；移動欄位命名為「直線移動時間」，值為 `m`。
- 開啟功能時顯示即時計算文案：`先等待 n 秒，再以 15 km/h 移動 m 秒，共 n+m 秒`。
- 關閉功能時顯示：`到站後等待 n 秒`。
- 移除半徑輸入與 radius state/API 傳遞。
- 將功能名稱改為「到站後直線移動」或等義名稱。
- 套用按鈕同時套用 enabled 與 `n`，成功提示改成「下一個停靠點起生效」。
- StatusBar 應在 movement phase 顯示當下 15 km/h；原地等待時顯示 0，而不是一直顯示路徑 preset 速度。

涉及：

- `frontend/src/extensions/custom/jumpRandomWalk/JumpRandomWalkControl.tsx`
- `frontend/src/extensions/custom/jumpRandomWalk/api.ts`
- `frontend/src/hooks/useSimulation.ts`
- `frontend/src/services/api.ts`
- `frontend/src/components/ControlPanel.tsx`
- `frontend/src/App.tsx`
- `frontend/src/i18n/strings.ts`

### 第六階段：測試與文件

後端自動測試至少覆蓋：

- `m` 秒後距離約 `4.1667×m` 公尺，所有 tick bearing 相同。
- `n=0` 時會直接移動 `m` 秒；`m=0` 時只等待且不抽 bearing；兩者皆為 0 時不執行 dwell。
- 開啟功能時總 dwell 為 `n+m`。
- pause 凍結位置與兩個 phase 的剩餘時間，resume 沿原方向續走。
- stop 在 movement 與 idle wait 都能立即結束。
- hot apply 只影響下一站。
- 舊 pre/post request 正確正規化為新 `n`。
- 非循環最後一點精確停止。
- 閉環回 waypoint 0 不重複 teleport，圈數與完成事件正確。
- 推送暫時失敗會重試，永久失敗會回 IDLE 並送出 simulation error。

前端驗證至少包含 TypeScript、production build、localStorage migration，以及 `n+m` 顯示在 enabled／disabled／running 狀態下都正確。

文件同步：

- README／README.en
- `frontend/src/i18n/strings.ts`
- `doc/custom-feature-ledger.md`
- `doc/progress.md`
- 本文件的實作結果與實機驗證紀錄

## 主要邏輯風險與處理

1. **移除 pre-delay 後立即跳點**：開始路徑或上一站 dwell 結束時會立刻 teleport；這是新語意，不是回歸。UI 應不再顯示任何跳躍前倒數。
2. **總行程會增加 `m` 秒／站**：若 `n` 由舊 pre+post 合併而來，開啟功能後會多出 movement `m` 秒；ETA 必須同步反映。
3. **閉環起點重複處理**：必須調整 traversal，不能只刪除 pre-delay 參數。
4. **有限圈數的結束位置**：最後回到 waypoint 0 後不能再執行 `n+m` post-dwell，否則完成位置偏離起點。
5. **暫停後多走一步**：tick wait 必須同時監聽 pause/stop，並以有效 elapsed 計算座標。
6. **I/O 延遲降低速度**：使用 deadline-based 排程，而不是 sleep 後再累加耗時。
7. **狀態列速度錯誤**：前端需要讀當下 position event speed，而非只顯示 route effectiveSpeed。
8. **接手快照不完整**：若主裝置在 movement 中斷線，現有 snapshot 沒有 bearing、phase 與 elapsed；本次若要保證無縫接手，需一併擴充 snapshot，否則可定義接手從下一站重新開始。
9. **直線穿越不合理地形**：固定 geodesic 不看道路、水域或建物，屬已知產品限制。
10. **0.5 秒推送負載**：每站約 8 次 movement push，多裝置時倍增；需以實機確認 Wi-Fi tunnel 穩定性。

## 建議實作順序與驗收門檻

1. 先完成 pure policy 與 legacy contract 正規化測試。
2. 再改 post-dwell state machine，讓 pause/stop／n+m 時序測試通過。
3. 接著整理 loop traversal、ETA 與最後一點規則。
4. 後端穩定後再切換前端 UI、localStorage migration 與 hot apply。
5. 跑 backend tests、extension boundary、Pyright、Mypy、TypeScript 與 production build。
6. 最後以一台 iPhone 驗證實際速度與設定的 `m` 秒位移，再以兩台裝置驗證推送負載及 hot apply。

下方接續記錄實作進度與驗證結果；前述內容保留為需求與驗收基準。

## 實作進度

### 2026-07-18 第一階段：domain contract 與舊版相容

- 後端啟動 contract 已改用 `jump_dwell_motion` 與 `jump_extra_wait`，預設額外等待為 6 秒。
- `LoopRequest`／`MultiStopRequest` 仍接受舊 `jump_random_walk`、`jump_pre_delay`、`jump_post_delay`；新欄位不存在時會正規化為 `jump_extra_wait = max(pre, 0) + max(post, 0)`，新舊欄位同時存在則以新欄位為準。
- runtime engine、loop、multi-stop 與 location API 已接上新欄位；舊 radius 不再進入 runtime。
- hot-apply schema 接受新舊開關。舊前端沒有傳 `n` 時只切換 movement enabled，不會把當前額外等待覆寫成預設值；paused route 也允許套用。
- 新增 contract regression tests；`backend/tests/extensions/test_jump_random_walk.py` 共 4 項通過，backend compileall 通過。
- 此階段先保留舊隨機座標 policy，下一階段才替換為固定 bearing movement session。

### 2026-07-18 第二階段：固定 bearing movement policy

- custom extension 新增 `DwellMotionSession` 與固定常數：15 km/h、4 秒、0.5 秒 tick。
- session 建立時只呼叫一次 random source 產生 bearing；所有座標都從原始到站座標按累積有效秒數計算，不逐點累加、不加入 jitter。
- elapsed 小於 0 會夾到 0，超過 4 秒會夾在終點；終點距離約 16.67 m。
- 新增固定 bearing、累積距離、單次 random call 與 4 秒終點 clamp 測試；extension 測試共 6 項通過，extension boundary check 通過。
- 舊 `perform_dwell_step()` 暫時仍存在供核心使用；第三階段接上新 session 後移除。

### 2026-07-18 第三、四階段：post-dwell 狀態機與 traversal

- 舊 `jump_wait()`／`perform_dwell_step()`／`random_coordinate()` 已移除；Flower 的一般等待改用獨立 `interruptible_wait()`，避免被 jump 專用語意污染。
- jump route 不再執行任何 pre-delay；每站在 arrival events 後依序執行固定方向 movement 與額外 idle wait。
- engine 新增 pause change signal 與累積 pause clock。movement／idle wait 都以 wall clock 扣除 pause interval 計算有效時間，pause 不會再多走一個 tick，stop 可喚醒等待。
- movement 位置推送具三次有限重試，tick 使用 monotonic active elapsed；push／emit 耗時不會被額外加在固定 sleep 後面。
- position events 增加 `dwell_phase`、`dwell_remaining_seconds`、movement bearing 與即時 speed；movement 完成後 `_current_speed_mps` 歸零。
- ETA 統一使用 `motion_enabled ? 4+n : n`；jump route 的 distance 統計維持 0，避免 dwell 位移污染點對點路徑距離。
- non-loop multi-stop 最後一點維持精確停止、不執行 post-dwell；loop 模式第二圈後會從 waypoint 0 正確回到完整點序。
- closed loop 回 waypoint 0 後不再重複 teleport；有限圈數到達上限時不執行 waypoint 0 dwell，精確停在起點。
- 新增 movement+idle 時序、stop、pause freeze、有限圈 closure 與最後點 regression tests。完整 backend tests 18 項通過，compileall 與 extension boundary check 通過。

### 2026-07-18 第五階段：前端設定、遷移與即時速度

- Jump API、useSimulation、ControlPanel 與 App 已改用 `jump_dwell_motion`／`jump_extra_wait`；所有 pre-delay、post-delay 舊資料流與 radius UI／request 已移除。
- localStorage 新增 `locwarp.jump.dwell_motion` 與 `locwarp.jump.extra_wait`。新 key 不存在時，movement enabled 從舊 random-walk key 遷移，`n` 從舊 pre+post 相加後寫入。
- 控制面板只保留「到站後直線移動」與「移動後額外等待 n 秒」，並依開關即時顯示 `4+n` 或 `n` 的總到站後時間。
- hot apply 單裝置與多裝置都會同時傳 enabled 與 `n`，成功提示明確說明從下一個停靠點起生效。
- jump dwell position event 會驅動 `dwellSpeedKmh`；StatusBar 在 movement／idle／paused 時顯示實際 15／0 km/h，其他移動模式仍使用既有 effective speed。
- 中英文 i18n 已改成新語意；前端 `tsc --noEmit` 通過。

### 2026-07-18 第六階段：最終驗證

- Backend pytest：18 passed。
- Backend Pyright：0 errors、0 warnings、0 informations。
- Extension boundary check：通過。
- Backend compileall：通過。
- Electron main syntax：通過。
- Frontend TypeScript：通過。
- Frontend production build：通過；僅保留既有的 API dynamic/static import 與大 chunk 警告。
- README 中英文、custom feature ledger 與 `doc/progress.md` 已同步新語意。
- 尚待實機驗證：iPhone 實測 15 km/h／4 秒位移、Wi-Fi tunnel 0.5 秒推送穩定度，以及雙裝置各自隨機 bearing 的操作體驗。

### 2026-07-18 後續調整第一段：可設定移動秒數的後端契約

- 使用者已確認原本「到站後固定方向 15 km/h 移動 4 秒」在單台與雙台實機測試均正常。
- 新需求將停留順序調整為「到站 → 等待 n 秒 → 隨機選一次方向 → 固定 15 km/h 直線移動 m 秒 → 下一次跳躍」。
- 後端啟動 request、runtime engine 與 hot-apply contract 已新增 `jump_move_seconds`；預設 4 秒、最小值 0，舊客戶端未傳欄位時維持原本 4 秒。
- 狀態機、前端 UI 與完整 regression tests 尚在後續小段實作中；前述實機結果只代表調整前版本，新順序完成後仍需再驗證。

### 2026-07-18 後續調整第二段：等待優先的 post-dwell 狀態機

- multi-stop 與 route-loop 啟動時會保存 `jump_move_seconds`，每次到站再快照 enabled、`n`、`m`，hot apply 維持下一站邊界生效。
- 每站流程已改成先執行可 pause／stop 的 idle wait，等待完成後才建立 `DwellMotionSession` 並抽一次 bearing，再以固定 15 km/h 移動 `m` 個有效秒。
- ETA 與 countdown 總時間使用 `motion enabled ? n+m : n`；idle event elapsed 為 `0..n`，movement event elapsed 為 `n..n+m`，movement 完成後送出 `complete` phase 並將速度歸零。
- `m=0` 時不建立 movement session，也不抽方向；`n=0` 時會直接進入 movement。pause 仍凍結當前階段的有效時間。

### 2026-07-18 後續調整第三段：後端 regression tests

- 新增 custom duration policy test：`DwellMotionSession` 會在使用者設定的 `m` 秒終點 clamp，位移仍為 `15 / 3.6 × m` 公尺。
- post-dwell 時序測試改為明確傳入短 `m`，並驗證第一個 dwell phase 是 idle、moving 只在等待完成後出現。
- contract tests 驗證舊 request 未傳 `jump_move_seconds` 時預設 4 秒，新 request 可覆寫；舊 hot apply 未傳 `m` 時不覆寫 runtime 值。
- `backend/tests/extensions/test_jump_random_walk.py`：11 passed。

### 2026-07-18 後續調整第四段：前端可設定 `m`

- `useSimulation` 新增 `jumpMoveSeconds`，以 `locwarp.jump.move_seconds` 保存，預設 4 秒；所有單台／雙台 loop 與 multi-stop request 都會傳 `jump_move_seconds`。
- hot apply 會同時套用 enabled、`n`、`m`，從下一個停靠點的快照邊界生效。
- 控制面板依實際執行順序顯示「到站後先等待 n 秒」→「等待後直線移動」→「直線移動時間 m 秒」；移動未啟用時 `m` 輸入停用但設定值保留。
- 中英文摘要改為「先等待 n 秒，再以 15 km/h 移動 m 秒，共 n+m 秒」。Frontend `tsc --noEmit` 通過。

### 2026-07-18 後續調整第五段：文件與完整驗證

- README 中英文與 custom feature ledger 已改成目前的「先等待 `n`、再移動 `m`」語意；速度維持固定 15 km/h，`m` 預設 4 秒。
- Backend tests：19 passed；extension boundary check 與 Pyright（0 errors／warnings／informations）通過。
- Electron syntax、Frontend TypeScript 與 Vite production build 通過；只有既有的 Vite CJS API deprecated、API 混合 dynamic/static import 與大 chunk 警告。
- `git diff --check` 通過；既有不相關的 untracked 文件 `doc/2026-07-16-route-start-index-log-audit.md` 保持未修改。
- 實機驗收完成：使用者確認現行新順序與可調 `m` 版本在單台、雙台裝置皆正常，本次功能可提交保存。
