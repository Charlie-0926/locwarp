# 客製功能帳本

更新日期：2026-07-15

狀態定義：

- `local-only`：僅客製版提供，放入 extension 層維護。
- `upstream-candidate`：通用能力，適合整理後提交官方。
- `available-upstream`：官方已包含，下一次同步時移除本機重複 patch。
- `integration`：客製版基礎設施，保留小型整合 commit。

| 功能 | 狀態 | 主要檔案 | 後續處理 |
|---|---|---|---|
| Spiral／中心繞圈 | local-only | `backend/extensions/custom/spiral/`、`frontend/src/extensions/custom/spiral/` | 已完成第一階段 extension 遷移；核心只保留穩定接點 |
| 等待期間隨機漫步 | local-only | `backend/extensions/custom/jump_random_walk/`、`frontend/src/extensions/custom/jumpRandomWalk/` | 已抽出 dwell policy、schema、API adapter 與控制面板；核心只保留呼叫接點 |
| 多裝置狀態同步與接手 | local-only | `backend/extensions/custom/multi_device/`、`frontend/src/extensions/custom/multiDevice/` | coordinator、runtime、fan-out 與啟動前對齊已抽離；`main.py` 僅保留相容 wrapper |
| 2-opt 路徑最佳化 | upstream-candidate | `backend/extensions/custom/route_optimizer/`、`frontend/src/extensions/custom/routeOptimizer/` | 已獨立並補單元測試；未來可直接整理成 upstream PR |
| 單一執行個體鎖 | upstream-candidate | `instance_lock.py`、`main.py`、`start.py`、Electron main | 保留獨立 integration commit，可提官方 |
| 套用速度跨路徑點維持 | available-upstream | `simulation_engine.py`、`route_loop.py`、`multi_stop.py` | 官方 v0.2.189 已提供；同步後採官方實作 |
| Pyright／mypy 型別修正 | upstream-candidate | 多個 backend service/core 檔案 | 依模組拆成小 commits，優先提交官方 |
| 打包與啟動器調整 | integration | `build-installer.bat`、`LocWarp.bat`、`start.py` | 與功能 extension 分開維護 |

## 基線

- 官方共同基底：`v0.2.177`（commit `53042c6`）
- 官方鏡像分支：`main` → `upstream/main`
- 客製發布分支：`custom/main`
- 建立基線時官方最新：`v0.2.190`（commit `c1a6c36`）

## 自動化保護

- `scripts/check-extension-boundaries.ps1` 防止已抽離功能重新滲回官方核心檔案。
- `.github/workflows/custom-compatibility.yml` 在 `custom/main` push 時執行 extension tests、Mypy、Pyright、TypeScript 與 production build。
- `scripts/rehearse-upstream.ps1` 使用 `git merge-tree` 預演官方更新，不改動目前工作樹。
