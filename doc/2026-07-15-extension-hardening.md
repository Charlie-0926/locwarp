# 客製擴充模組強化紀錄

日期：2026-07-15

## 完成內容

- Jump Random Walk：backend 的 dwell policy、request schema、API route，以及 frontend API/control UI 已移入 extension。
- 2-opt：演算法與 frontend API adapter 已移入 route optimizer extension，官方 geo service 不再承載客製演算法。
- 多裝置同步：backend 自動同步、進度鏡像、primary follower 已移入 coordinator；frontend runtime、fan-out 與啟動前對齊已移入 extension。
- 客製 location router：Jump 與 Spiral endpoint 由獨立 router builder 註冊，官方 location API 僅保留單一 include 接點。
- 修正多裝置 ETA 鏡像：不再寫入唯讀衍生 property，改同步 tracker 的可變來源欄位。
- 加入 extension 單元測試、邊界檢查與 GitHub Actions compatibility workflow。

## 衝突面縮減

本輪從既有官方／核心檔案移除大量客製實作，讓 `main.py`、`ControlPanel.tsx`、`useSimulation.ts`、`geo_extras.py` 與 `location.py` 只保留較小的穩定整合點。客製功能新增檔案位於 `backend/extensions/custom/` 與 `frontend/src/extensions/custom/`，官方更新通常不會直接修改這些路徑。

## 驗證

- GitHub Actions：extension pytest、全 backend Mypy、backend Pyright、frontend TypeScript 與 production build 全部通過。首次執行揭露的 `instance_lock.py` 跨平台 `ctypes` stubs 差異及 `gpx_service.py` loop variable 型別收窄已修正。
- Extension boundaries：通過。
- Backend Pyright：0 errors、0 warnings。
- Frontend TypeScript：通過。
- Electron syntax：通過。
- Vite production build：通過；只有既有 chunk size/dynamic import 警告。
- `git diff --check`：通過。
- Upstream merge-tree rehearsal：目前 `custom/main` 與 `upstream/main` (`c1a6c36`) 無衝突。
- 本機缺少 Python interpreter；pytest/Mypy 已由 GitHub Actions 的 Linux/Python 3.11 環境執行並通過。
- 實機行為仍需兩台 iPhone 驗證多裝置接手、等待期間 hot apply 與 route waypoint 切換。
