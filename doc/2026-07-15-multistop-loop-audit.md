# 多點路徑圈數功能檢查

## 結論

目前 `custom/main` 仍保留多點路徑的圈數控制，功能沒有從程式碼或打包前端消失。

## 已確認項目

- `frontend/src/App.tsx` 有「圈數」欄位：`0` 代表單趟、正整數代表指定圈數、留白代表無限循環。
- `frontend/src/hooks/useSimulation.ts` 會保存 `loopLapCount`，並把設定傳給後端 API。
- `backend/models/schemas.py` 的 `LoopRequest` 仍有 `lap_count`。
- `backend/core/route_loop.py` 仍會在達到圈數後自動停止並送出 `loop_complete`。
- `frontend/dist/assets/index-BQ9WGcZy.js` 仍包含圈數控制相關內容。

## 注意

v0.2.177 起，原本分開的「多點導航」與「路線巡迴」合併為同一個「多點路徑」模式；圈數欄位現在位於該模式的路徑點設定區，不再是獨立模式。

本次僅完成診斷，未修改程式碼。

## 安裝包驗證補充

- `frontend/release/LocWarp Setup 0.2.190.exe` 建置時間為 2026-07-15 16:32，大小 150,117,817 bytes。
- 對應的 `win-unpacked/resources/app.asar` 內含 `dist/assets/index-BQ9WGcZy.js`。
- 直接讀取安裝包內的 JavaScript，確認仍包含 `圈數`、`單趟`、`無限循環`、`lap_count` 與 `loopLapCount`。

## 執行中修改行為

- 目前修改圈數只更新前端狀態與 localStorage，不會即時送到正在執行的後端路徑。
- `lap_count` 只在按下開始時隨 `/api/location/loop` 請求傳送；執行中目前只有速度與跳躍設定有獨立的套用流程。
- 因此執行中的路徑會繼續使用啟動當下的圈數設定；修改後需停止並重新開始才會生效。
