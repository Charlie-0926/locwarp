# 400+ 點路徑最佳化與 LKH-3 評估

日期：2026-07-16

## 結論

- LKH-3 的搜尋能力與大規模解品質會優於目前的 nearest-neighbor + 2-opt，但不建議直接取代現行實作。
- 目前 400+ 點變慢的首要原因是 2-opt 實作對每一組候選都複製完整順序，並以 O(n) 重新計算整條路徑成本；這讓一次候選掃描成為 O(n³)，且每次接受改善後又從頭掃描。
- 第一階段應先優化既有 2-opt 的候選成本計算、加入停止條件與基準測試。若真實資料顯示解品質仍不足，再以可選 solver adapter 評估 LKH 類或授權相容的替代方案。
- LKH-3 僅允許研究／學術及非商業使用，LocWarp 本身採 MIT 並允許商業使用；若將 LKH-3 binary/source 隨 LocWarp 發布，會造成授權與散布範圍不相容，必須先取得額外授權或改選相容方案。

## 現行流程

1. `/api/geocode/route-optimize` 先建立完整的 n × n duration matrix。
2. 8 點以下使用 exact permutation；超過 8 點使用 `optimize_order_2opt()`。
3. 2-opt 先以 nearest-neighbor 建立初始開放路徑，再以 first-improvement 反轉片段。
4. `keep_first=True` 時固定索引 0 為起點；終點不固定，而且成本不包含終點返回起點。

400 點時 matrix 有 160,000 個元素。OSRM public table 超過 100 點會直接跳過；依 engine 可能再嘗試 Valhalla，失敗時使用 haversine。因此使用者看到的等待時間可能同時包含 matrix provider 與 solver，正式決策前應分段計時。

## 已確認的效能問題

現行每一個 `(left, right)` 候選都會：

- `candidate = order[:]`：O(n)；
- 反轉並寫回片段：O(n) 最壞情況；
- `_route_total(...)`：O(n)。

一輪約檢查 O(n²) 個候選，所以完整一輪約 O(n³)；接受改善後重新掃描，使總耗時可能更高。固定亂數、對稱 Euclidean matrix 的本機唯讀基準結果：

| 點數 | 現行 2-opt 時間 |
|---:|---:|
| 50 | 0.018 秒 |
| 100 | 0.259 秒 |
| 200 | 5.967 秒 |

這不是嚴格的 400 點預測，但已顯示成長遠快於平方級；因此目前沒有足夠證據認定必須換 solver，先修正實作即可取得很大的改善空間。

### 實際 434 點改善前基準

使用本機 `doc/coordinates.txt`，以 `foot` profile 的 haversine duration matrix、`keep_first=True` 執行；座標內容未輸出或上傳：

| 項目 | 結果 |
|---|---:|
| 有效座標 | 434 點 |
| matrix 建立 | 0.037 秒 |
| nearest-neighbor 距離 | 75,489.419 公尺 |
| 舊版 2-opt solver | 134.100 秒 |
| 舊版 2-opt 距離 | 63,297.434 公尺 |
| 路徑驗證 | 434 點各一次、固定起點正確 |

### 增量成本 2-opt 改善後

以相同 matrix 與固定起點條件重跑；最終版連跑 5 次為 1.391、1.382、1.382、1.386、1.410 秒，中位數 1.386 秒：

| 比較項目 | 舊版 | 新版 |
|---|---:|---:|
| solver 耗時 | 134.100 秒 | 1.386 秒（5 次中位數） |
| 相對速度 | 1× | 96.7× |
| 耗時降低 | — | 98.97% |
| 最終距離 | 63,297.434 公尺 | 63,297.434 公尺 |
| 路徑合法性 | 通過 | 通過 |
| 固定起點 | 通過 | 通過 |

新版 5 次產生完全相同的順序。私有座標檔已加入 `.gitignore`，本文件與測試不含座標內容。

## LKH-3 的適配性

優點：

- Lin-Kernighan 的可變深度 k-opt 與 candidate sets 通常比單次 nearest-neighbor + 2-opt 找到更好的 tour。
- 400 點對原生 C solver 並非大規模，可透過 trials、runs、candidate 數及 time limit 控制品質／等待時間。
- 可處理對稱與非對稱 TSP，也支援多種受限 TSP／VRP 變體，未來若加入時間窗、容量、多車等限制，能力較完整。

整合風險：

- LocWarp 現在求解的是「開放 Hamiltonian path」，不是 LKH 預設的封閉 TSP tour。需加入 dummy node；固定起點時還要強制 dummy 與起點的邊，移除 dummy 後才能還原固定起點、自由終點的 path。
- Valhalla duration matrix 可能是非對稱成本，不能假設反向路段等價；需輸出 ATSP 或先明確定義對稱化策略。
- TSPLIB explicit matrix 通常使用整數成本，浮點 duration 必須縮放、取整並檢查溢位及排序誤差。
- LKH-3 是外部原生 executable，不是目前 requirements 中的純 Python 套件。Windows x64、PyInstaller、Electron/NSIS 都需額外打包 binary，並處理暫存 instance/parameter/tour files、timeout、取消、併發與錯誤 fallback。
- LKH-3 的研究／非商業授權與本專案 MIT 商用授權不相容，是目前最大的採用阻礙。

## 建議的決策順序

1. 先在 route optimize API 加入 matrix acquisition、matrix build、initial nearest-neighbor、local search 的分段計時（未在本輪實作）。
2. 保留現有 solver 介面，將 2-opt 改為增量成本比較；只在接受交換時反轉路徑，並加入 time budget／max passes。
3. 使用實際 100／200／400+ 點資料比較 wall time、路徑成本、是否固定起點、是否每點恰好一次，以及 deterministic behavior。
4. 若速度已達標但品質不足，再做 solver adapter POC。LKH-3 只有在確認非商業使用或取得授權後才列入；否則優先評估授權相容的 solver。
5. POC 必須讓外部 solver 失敗或超時時安全退回本機 2-opt，不能讓「最佳順序」API 失敗。

## 本輪範圍

- 第一階段先完成唯讀分析；後續依使用者指示實作增量成本 2-opt、不可達邊防護及 regression tests。
- 未修改 frontend、API contract 或 matrix provider；私有座標未上傳。
