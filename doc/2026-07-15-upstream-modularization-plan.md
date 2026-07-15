# LocWarp 客製版與官方版整合方案

日期：2026-07-15

## 結論

可行，建議採用「薄分支（thin fork）＋客製擴充層＋固定 upstream 同步流程」，而不是把整份客製版長期當成一個巨大 patch。

短期先恢復完整 Git 歷史與分支管理；中期將新增模式及 UI 拆到獨立 extension 目錄；通用 bug 修正則優先交回官方或在官方吸收後移除本機 patch。目標是每次官方更新只需處理少數 adapter／bootstrap 檔案，而不是重新合併所有客製程式。

## 現況盤點

- 本機 `frontend/package.json` 版本為 `0.2.177`；官方最新檢查到 `0.2.190`。
- 本機雖有 `.git` 目錄，但目錄內容為空，`git rev-parse` 回報不是 Git repository。目前無法安全執行 fetch、merge、rebase 或追蹤共同祖先。
- 客製功能目前至少影響 13 個會與上游重疊的檔案。
- 四個主要熱點已非常大型：
  - `backend/core/simulation_engine.py`：1175 行
  - `frontend/src/App.tsx`：2855 行
  - `frontend/src/hooks/useSimulation.ts`：1174 行
  - `frontend/src/components/ControlPanel.tsx`：1303 行
- 客製內容包含 Spiral、等待期間隨機漫步、2-opt、雙裝置同步、單一執行個體、速度套用修正及型別修正等。
- 官方 v0.2.189 已加入「新速度跨路徑點維持、停靠等待期間可套用」修正，因此本機同類 patch 後續應改採官方版本，避免維護重複實作。
- 官方 v0.2.190 又修改前端裝置狀態與 i18n，顯示官方仍會持續改動客製版也常碰觸的區域。

## 建議的 Git 結構

```text
keezxc1223/locwarp:main  (upstream，官方)
             |
             v
本方 fork: main          (只鏡像官方，不放客製 commit)
             \
              custom/main (可發布的客製版)
                 + feature/spiral
                 + feature/jump-random-walk
                 + feature/multi-device-sync
                 + fix/single-instance
```

遠端命名：

- `upstream`：`https://github.com/keezxc1223/locwarp.git`
- `origin`：本方建立的 GitHub fork

`main` 僅追蹤官方，`custom/main` 才包含客製功能。每個客製功能使用小而單一目的的 commit；長期客製分支建議定期 merge `upstream/main`，保留實際整合歷史。啟用 `git rerere`，可重用反覆出現的衝突解法。

## 程式架構

### Backend

建議新增：

```text
backend/extensions/
  registry.py
  contracts.py
  custom/
    spiral/
      handler.py
      schemas.py
      router.py
    jump_random_walk/
    multi_device_sync/
```

- `SimulationEngine` 保留生命週期、裝置與移動的共用協調責任。
- 模式透過 registry 註冊，使用一致介面，例如 `start`、`pause`、`resume`、`stop`、`snapshot`。
- 客製 API 集中到一個 extension router；官方 `main.py`／router 聚合處只保留一個匯入點。
- Spiral 的 handler、request schema 與 API 不再分散修改 `simulation_engine.py`、`schemas.py`、`location.py`。
- 速度 profile、暫停、斷線恢復等共同行為留在核心 service，不複製到每個模式。

### Frontend

建議新增：

```text
frontend/src/extensions/
  registry.ts
  contracts.ts
  custom/
    spiral/
      descriptor.tsx
      panel.tsx
      api.ts
      strings.ts
    jumpRandomWalk/
```

每個 mode descriptor 至少描述：

- mode id 與顯示名稱
- 設定面板元件
- 預設值與 localStorage key
- 啟動／停止 API adapter
- 地圖與狀態列呈現方式
- i18n 字串

`App.tsx`、`useSimulation.ts`、`ControlPanel.tsx` 改為讀取 registry，不再為每個客製模式增加大量 `if/else`、props 和 switch case。這三個檔案仍可能與官方衝突，但只保留少量穩定的擴充接點。

## 功能分類原則

| 類型 | 處理方式 | 範例 |
|---|---|---|
| 客製產品功能 | 放進 extension | Spiral、等待期間隨機漫步、雙裝置同步 |
| 通用演算法能力 | 獨立 service，盡量提交官方 | 2-opt |
| 通用 bug fix | 提交／追蹤官方；官方吸收後刪除本機 patch | 速度維持、單一執行個體 |
| 純型別與相容性修正 | 小型獨立 commit，優先 upstream | Pyright、mypy 修正 |
| 客製品牌與設定 | manifest／config 驅動 | 名稱、預設值、功能開關 |

建議建立 `doc/custom-feature-ledger.md`，每項標記：`local-only`、`submitted-upstream`、`available-upstream`、`drop-after-sync`、`conflicted`。速度修正目前應標記為 `available-upstream`。

## 官方更新流程

1. `git fetch upstream --tags`
2. 將本方 `main` fast-forward 到 `upstream/main`。
3. 建立 `sync/upstream-vX.Y.Z` 暫存分支。
4. 在暫存分支把 `upstream/main` merge 到 `custom/main`。
5. 解決 adapter／bootstrap 衝突並記錄在同步報告。
6. 執行 backend 型別檢查、frontend `tsc`、Vite build、Electron 語法與必要的行為測試。
7. 確認 feature ledger，刪除已被官方吸收的重複 patch。
8. 通過後才合併回 `custom/main` 並打客製版 tag。

不要讓排程直接自動合併到可發布分支。可以用 CI 定期做「試合併」並產生衝突報告，但仍由人工確認行為差異。

## 遷移階段

### Phase 0：建立可信任基線

- 在另一個安全目錄 clone 官方 v0.2.177（或能確認的真正共同基底）。
- 將目前工作目錄當作客製快照，使用檔案 diff 重建一組有意義的客製 commits。
- 不直接覆蓋目前工作目錄；先備份並排除 `node_modules`、build artifact、秘密設定。
- 建立本方 GitHub fork，設定 `origin`／`upstream`。

### Phase 1：建立功能帳本與測試門檻

- 將每個差異歸屬到一個功能或修正。
- 先把速度修正換成官方 v0.2.189 實作並移除重複差異。
- 固化現有 `check_project.py`、Pyright、mypy、tsc、Vite build 檢查。

### Phase 2：抽離 Backend extension

- 先抽 Spiral，因為已有獨立 `spiral_walk.py`，最適合作為第一個 registry 範例。
- 再抽等待期間隨機漫步及雙裝置同步。
- 將核心檔案的客製修改縮成註冊與 hook。

### Phase 3：抽離 Frontend extension

- 建立 mode registry 與 extension API。
- 將 Spiral panel、狀態、i18n、啟動 handler 移出大型核心元件。
- 用同樣模式處理後續客製功能。

### Phase 4：自動化 upstream rehearsal

- 加入手動／排程 CI：抓取官方、在暫存 branch 試 merge、執行檢查、輸出衝突檔案。
- 維護 `doc/upstream-sync/`，每次更新記錄官方版本、衝突、移除的本機 patch 與測試結果。

## 驗收標準

- 官方小版本更新時，多數客製 extension 檔案無衝突。
- 一般更新的衝突集中在約 2～5 個 adapter／bootstrap 檔案。
- 可清楚回答目前客製版基於哪個官方 commit。
- 可逐項辨識客製功能是否已被官方吸收。
- 同步後可由固定命令完成型別、build 與核心行為驗證。

## 2026-07-15 實作進度

- Phase 0、Phase 1 已完成：fork/remotes、官方鏡像分支、客製分支、feature ledger 與固定驗證腳本均已建立。
- Phase 2、Phase 3 的主要拆分已完成：Spiral、Jump Random Walk、2-opt 與多裝置 coordinator/runtime 已有 backend/frontend extension 邊界。
- Phase 4 已完成第一版：本機 upstream rehearsal、extension boundary check 與 GitHub Actions compatibility workflow 已加入。
- 尚未完全消除的核心差異屬跨切面整合點，例如 simulation state、route resume、WebSocket 狀態事件與 UI mode wiring；這些差異由邊界檢查、rerere 與同步演練共同保護。

## 下一步建議

每次官方發布後依 `doc/upstream-sync/README.md` 執行 rehearsal 與暫存分支合併。若某個通用修正已進入 upstream，先從 feature ledger 標記並刪除重複 patch，再發布新的客製版 tag。
