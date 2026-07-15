# v0.2.190 客製功能合併稽核

日期：2026-07-15

## 結論

五類客製功能的 backend、API 與 frontend 程式路徑均保留在 `custom/main`，沒有在官方 v0.2.190 合併時遺失。靜態檢查與 production build 通過；多裝置接手機制仍需要兩台實機做最終行為驗收，Mypy 因本機沒有可用 Python interpreter 而未能在本輪重跑。

| 功能 | 程式合併 | 模組化 | 本輪驗證 |
|---|---|---|---|
| 中心繞圈 Spiral | 完整 | 已移至 backend/frontend extension | Pyright、tsc、build 通過；未做 iPhone 實走 |
| Jump Random Walk | 完整 | 已移至 backend/frontend extension | dwell policy、schema、API、hot apply 與控制面板已抽離；未做 iPhone 實走 |
| 2-opt 最佳路徑 | 完整 | 已移至 backend/frontend extension | 演算法與 API adapter 已獨立並補單元測試；build 通過 |
| 多裝置同步／UI 鏡像／接手 | 完整 | coordinator 與 frontend runtime 已移至 extension | snapshot/resume、leader handoff、position follower、runtime map、fan-out 均存在；需兩台實機驗收 |
| Pyright/Mypy 與 async 修正 | 完整保留 | 屬共用修正，不適合包成產品 extension | Pyright 0 errors；Mypy 因本機無 Python 未重跑 |

## GitHub fork 狀態

- `origin`：`https://github.com/Charlie-0926/locwarp.git`
- `upstream`：`https://github.com/keezxc1223/locwarp.git`
- `origin/main` 與 `upstream/main` 均為官方 v0.2.190 (`c1a6c36`)。
- 本機 `custom/main` 含本稽核文件 commit，完成後比 `origin/main` 多 5 個客製／整合 commits。
- 本輪將依使用者授權推送 `custom/main`，`main` 繼續保持官方鏡像，不混入客製提交。

## 驗證結果

- `scripts/verify.ps1`：通過。
- Pyright：0 errors、0 warnings。
- TypeScript `tsc --noEmit`：通過。
- Vite production build：通過；僅既有 dynamic import 與 chunk size 警告。
- Electron `node --check`：通過。
- Git conflict markers：0。
- Mypy：未執行，`py` 回報沒有已安裝的 Python。
- Extension boundary check：通過。
- 客製 extension 單元測試與 Mypy：交由 GitHub Actions 的 Linux/Python 3.11 環境執行。
