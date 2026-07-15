# Upstream 同步操作手冊

## 分支責任

- `main`：只鏡像 `upstream/main`，禁止直接開發或提交客製功能。
- `custom/main`：客製版的可發布分支。
- `sync/upstream-*`：每次官方更新的暫存整合分支。
- `feature/*`、`fix/*`：單一客製功能或修正。

## 日常檢查

只檢查目前官方是否可合併，不改變工作樹：

```powershell
.\scripts\rehearse-upstream.ps1
```

## 正式同步

工作樹乾淨且位於 `custom/main` 時執行：

```powershell
.\scripts\sync-upstream.ps1
```

腳本會抓取官方、更新乾淨 `main`、建立 `sync/upstream-*`、合併並執行驗證。若有衝突會停在同步分支，不會污染 `custom/main`；驗證通過後仍需人工 review，再依畫面提示 fast-forward 回 `custom/main`。

## 驗證

```powershell
.\scripts\verify.ps1
```

固定檢查 Pyright、Electron 語法、TypeScript 與 Vite production build。

## GitHub fork

目前只設定：

```text
upstream = https://github.com/keezxc1223/locwarp.git
```

建立本方 fork 後設定：

```powershell
git remote add origin https://github.com/<owner>/locwarp.git
git push -u origin main
git push -u origin custom/main
```

是否公開與 repository owner 必須由維護者決定，腳本不會自動建立或推送遠端 repository。
