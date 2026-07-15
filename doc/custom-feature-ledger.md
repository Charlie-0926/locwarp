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
| 等待期間隨機漫步 | local-only | `route_loop.py`、`multi_stop.py`、`useSimulation.ts`、`ControlPanel.tsx` | 抽成 route dwell policy extension |
| 多裝置狀態同步與接手 | local-only | `main.py`、`device.py`、`App.tsx`、`useSimulation.ts` | 抽成 lifecycle extension，保留單一 bootstrap hook |
| 2-opt 路徑最佳化 | upstream-candidate | `geo_extras.py`、`geocode.py` | 保持獨立 service，補測試後可提交官方 |
| 單一執行個體鎖 | upstream-candidate | `instance_lock.py`、`main.py`、`start.py`、Electron main | 保留獨立 integration commit，可提官方 |
| 套用速度跨路徑點維持 | available-upstream | `simulation_engine.py`、`route_loop.py`、`multi_stop.py` | 官方 v0.2.189 已提供；同步後採官方實作 |
| Pyright／mypy 型別修正 | upstream-candidate | 多個 backend service/core 檔案 | 依模組拆成小 commits，優先提交官方 |
| 打包與啟動器調整 | integration | `build-installer.bat`、`LocWarp.bat`、`start.py` | 與功能 extension 分開維護 |

## 基線

- 官方共同基底：`v0.2.177`（commit `53042c6`）
- 官方鏡像分支：`main` → `upstream/main`
- 客製發布分支：`custom/main`
- 建立基線時官方最新：`v0.2.190`（commit `c1a6c36`）
