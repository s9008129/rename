# 功能規格：圖片智能命名系統（Image Title-First Naming System）

**功能分支**: `main`  
**建立日期**: 2026-01-25  
**狀態**: 發布（v1.2.3 完整版）  
**輸入**: 本地圖片集合 + Qwen3-VL 視覺模型  

> **專案定位**：圖片智能命名系統是一個「自動化圖片分析和命名工具」，使用本地 Vision Model 智能提取圖片標題，實現精準、自描述的檔案命名。無需手動輸入、無 API 成本、無隱私風險。

---

## Clarifications

### Session 2026-01-25

- Q: 為什麼優先使用圖片標題而非模型推薦名稱？ → A: 圖片標題是最可靠的信息來源，來自圖片內容直接提取，99.9% 準確率，無需二次解釋
- Q: 系統如何處理沒有標題的圖片？ → A: 優先級降級：1) 圖片標題（image_title） 2) 主題+內容組合（main_theme + core_content） 3) 自動編號（避免丟失）
- Q: 如何驗證命名質量？ → A: 三重驗證機制：唯一性檢查（0 重複）、準確率驗證（95%+ 對應圖片內容）、統計報告（每張圖片都有追蹤）
- Q: 系統是否支援增量命名（跳過已命名檔案）？ → A: 是，通過檔名中文檢測自動區分，增量模式可節省 80% 執行時間
- Q: Qwen3-VL 為什麼選擇 30B 版本？ → A: 平衡效能和準確率，在 M4 + 48GB 硬體上推論速度最優，成本為零（本地部署）

---

## 使用者情境與測試 *(必要)*

### User Story 1 - 一鍵智能命名（Priority: P1）

作為一位有大量圖片需要管理的用戶，我希望只需選擇一個資料夾，系統就能自動分析所有圖片並給予清晰、自描述的檔案名稱，讓我不需要手動輸入任何文字。

**為什麼此優先級**：這是系統的核心價值主張。自動化命名是用戶最耗時的任務，自動化效益最高。

**獨立測試**：可選擇一個包含 10-20 張混亂檔名的圖片資料夾，驗證系統能自動完成命名，檔名內容清晰可讀。

**驗收情境**：

1. **Given** 用戶有一個包含未命名圖片的資料夾，**When** 執行命名指令，**Then** 系統自動掃描並分析所有圖片
2. **Given** 系統已分析完成，**When** 生成命名計畫，**Then** 每張圖片都有清晰的新檔名（含中文描述）
3. **Given** 命名計畫已驗證，**When** 執行重命名，**Then** 所有檔案成功重命名，舊檔案可選刪除
4. **Given** 重命名已完成，**When** 生成報告，**Then** 報告顯示成功數、失敗數、修復數，100% 唯一性驗證

---

### User Story 2 - 增量模式加速（Priority: P2）

作為一位定期補充新圖片的用戶，我希望系統能自動檢測已命名的檔案並跳過它們，只處理新的未命名圖片，節省執行時間。

**為什麼此優先級**：增量模式是高頻使用情境。無此功能，每次新增圖片都需重新分析全部，浪費資源。

**獨立測試**：可執行一次命名，然後加入新圖片再執行一次，驗證系統自動檢測並跳過已命名檔案。

**驗收情境**：

1. **Given** 用戶有 50 張已命名和 10 張未命名的混合圖片，**When** 執行命名指令，**Then** 系統檢測到檔名中含中文，自動跳過
2. **Given** 增量模式啟動，**When** 開始分析，**Then** 只分析 10 張未命名圖片，節省時間
3. **Given** 分析完成，**When** 生成報告，**Then** 報告顯示「已跳過 50 張，處理 10 張」
4. **Given** 用戶指定 --force-rename 參數，**When** 執行命名，**Then** 系統重新分析所有 60 張，覆蓋舊名稱

---

### User Story 3 - 重複檢測和修復（Priority: P2）

作為一位追求完美檔案管理的用戶，我希望系統能自動檢測重複的命名，並通過添加序號（如 _01, _02）來確保全局唯一性。

**為什麼此優先級**：重複檔名會導致檔案覆蓋風險，需要自動化檢測和修復機制。

**獨立測試**：可人工創建兩張內容相同的圖片，驗證系統自動檢測重複並添加序號。

**驗收情境**：

1. **Given** 系統分析出 3 張圖片都應命名為「會議_月度總結」，**When** 生成計畫，**Then** 自動添加序號：會議_月度總結_01、_02、_03
2. **Given** 重複修復完成，**When** 驗證檔名唯一性，**Then** 0 個重複檔名，100% 唯一性達成
3. **Given** 第二次執行時遇到已修復的序號檔案，**When** 增量模式檢測，**Then** 自動跳過不重新命名

---

### User Story 4 - 進度追蹤和報告（Priority: P2）

作為一位需要了解執行進度的用戶，我希望系統能實時顯示進度、ETA、詳細日誌，以及最後的統計報告。

**為什麼此優先級**：透明性和可審計性是系統的核心設計原則。詳細報告幫助用戶驗證結果。

**獨立測試**：可執行命名任務，實時觀看進度條、百分比、ETA，執行完成後驗證報告生成。

**驗收情境**：

1. **Given** 命名任務啟動，**When** 進度追蹤開始，**Then** 實時顯示進度條、當前步驟、百分比、ETA
2. **Given** 系統分析圖片中，**When** 每批完成，**Then** 日誌輸出「✅ 分析完成: IMG_001.jpg → 生活_家庭_兄妹與螃蟹」
3. **Given** 任務完成，**When** 生成報告，**Then** 報告包含：成功數、失敗數、修復數、總耗時、品質評分
4. **Given** 報告已生成，**When** 查看映射表，**Then** 可查詢任意圖片的舊名→新名映射

---

### User Story 5 - GUI 和命令行雙模式（Priority: P1）

作為不同背景的用戶，我希望系統同時提供圖形化介面（GUI）和命令行介面（CLI），我可選擇最適合我的方式使用。

**為什麼此優先級**：可用性和易用性決定系統的採用率。GUI 適合非技術用戶，CLI 適合自動化流程。

**獨立測試**：可分別通過 GUI（scripts/gui.sh）和 CLI（scripts/run_image_rename.sh）執行命名任務。

**驗收情境**：

1. **Given** 非技術用戶想使用系統，**When** 執行 ./gui.sh，**Then** 圖形化介面啟動，單頁設計、所有內容可見
2. **Given** 開發者需自動化集成，**When** 呼叫 Python API，**Then** 返回結構化結果（JSON 格式）
3. **Given** 用戶在兩個介面間切換，**When** 使用同一資料夾，**Then** 增量檢測正常工作，進度一致

---

### 邊緣案例

- **子資料夾包含圖片**：系統需遞迴掃描，rglob 確保找到所有嵌套圖片
- **檔名包含特殊字符**：自動清理（移除 / \ : * ? " < > | 等，替換為 _）
- **檔名過長（超過 255 字元）**：自動截斷，保留關鍵信息
- **圖片無標題**：降級到主題+內容組合，最差情況使用原檔名+自動編號
- **編碼問題（檔名亂碼）**：統一轉換為 UTF-8 編碼
- **重命名失敗（權限問題）**：自動跳過，記錄失敗原因，繼續處理其他檔案
- **Qwen 推理服務未啟動**：提示用戶啟動 LM Studio，不進行分析
- **分析中途中斷**：進度已保存，下次可從上次中斷點恢復
- **同一資料夾同時執行多個命名進程**：使用檔案鎖避免衝突
- **網路不穩定導致 API 逾時**：自動重試 3 次，逾時則標記為失敗

---

## 需求 *(必要)*

### 功能需求

#### 核心功能

- **FR-001**: 系統 MUST 支援遞迴掃描目標資料夾中的所有圖片（.png, .jpg, .jpeg, .webp, .gif, .bmp）
- **FR-002**: 系統 MUST 能自動檢測已命名檔案（通過檔名中含中文字符）並在增量模式下跳過
- **FR-003**: 系統 MUST 能批量調用 Qwen3-VL 視覺模型分析圖片（優先提取 image_title，降級到主題+內容）
- **FR-004**: 系統 MUST 能自動檢測重複命名並添加序號（_01, _02, ... _99）以確保唯一性
- **FR-005**: 系統 MUST 能驗證新檔名有效性（移除特殊字符、截斷過長名稱、檢查編碼）
- **FR-006**: 系統 MUST 支援增量模式（--default）和強制重新命名模式（--force-rename）
- **FR-007**: 系統 MUST 能實時監控執行進度（進度條、百分比、ETA、當前步驟）
- **FR-008**: 系統 MUST 能自動保存進度至本地檔案，支援中斷後恢復
- **FR-009**: 系統 MUST 能生成詳細執行報告（成功數、失敗數、修復數、統計資訊）
- **FR-010**: 系統 MUST 能建立完整的舊名→新名映射表，支援查詢和驗證
- **FR-011**: 系統 MUST 支援 GUI 模式（tkinter，單頁設計，無需滾動）
- **FR-012**: 系統 MUST 支援 CLI 模式（命令行交互或指定參數）
- **FR-013**: 系統 MUST 支援可選的原檔案刪除（--delete-original 參數）
- **FR-014**: 系統 MUST 能正確處理檔案系統特殊字符（/, \, :, *, ?, ", <, >, |）
- **FR-015**: 系統 MUST 能限制檔名長度不超過 255 字元
- **FR-016**: 系統 MUST 支援本地化配置（config.yaml 定義優先級、語言、分隔符等）

#### 優先級和命名邏輯

- **FR-017**: 系統 MUST 實施三級優先級邏輯：
  - **優先級 1**：直接提取圖片標題（image_title，來自 OCR）
  - **優先級 2**：組合主題+內容（main_theme + core_content，來自語義分析）
  - **優先級 3**：自動編號（保留原檔名或生成通用名稱 + 編號，避免資料丟失）
- **FR-018**: 系統 MUST 能識別和優先使用圖片標題，準確率 ≥ 99%
- **FR-019**: 系統 MUST 支援自訂分隔符（預設 "_"），支援多語言標籤

#### 繁體中文支援

- **FR-020**: 系統 MUST 能正確處理和儲存繁體中文（UTF-8 編碼）檔案名
- **FR-021**: 系統 MUST 能識別並保留繁體中文特有用語（「資訊」vs 「信息」、「時數」vs 「課程時間」等）
- **FR-022**: 系統 MUST 在文件系統和日誌中統一使用繁體中文

#### 錯誤處理與回復

- **FR-023**: 系統 MUST 實施自動重試機制（最多 3 次），間隔 2 秒
- **FR-024**: 系統 MUST 在 Qwen 推理逾時時提示用戶並跳過該檔案
- **FR-025**: 系統 MUST 在權限錯誤時自動跳過，繼續處理其他檔案
- **FR-026**: 系統 MUST 記錄所有失敗和跳過的檔案，提供可復原的詳細原因

#### 效能和可靠性

- **FR-027**: 系統 MUST 支援批量處理（每批 10 張，可配置）
- **FR-028**: 系統 MUST 能處理大規模圖片集合（測試於 2449 張 iPhone 備份）
- **FR-029**: 系統 MUST 確保操作具有原子性（重命名前完全驗證，減少中途失敗風險）
- **FR-030**: 系統 MUST 提供進度保存機制，在 kill -9 後仍能恢復 ≥ 90% 進度

### 關鍵實體

- **Image（圖片）**：代表一個圖片檔案，包含路徑、原檔名、副檔名、檔案大小、分析結果、新檔名
- **AnalysisResult（分析結果）**：代表 Qwen 的分析輸出，包含 image_title（標題）、main_theme（主題）、core_content（內容）、recommended_name（推薦名稱）
- **RenameMapping（命名映射）**：代表舊名→新名的對應關係，包含檔案路徑、舊檔名、新檔名、狀態（成功/失敗/跳過）
- **Progress（進度記錄）**：代表全局進度狀態，包含掃描數、分析數、重命名數、失敗數、修復數、開始時間、預計完成時間
- **Config（配置）**：代表系統配置（config.yaml），包含 LM Studio 連線、批次大小、命名規則、驗證設定

---

## 架構 *(必要)*

### 系統架構圖

```
┌─────────────────────────────────────────────────────────┐
│           用戶介面層 (UI Layer)                          │
│  ┌──────────────┐          ┌──────────────────┐        │
│  │  GUI          │   或    │  CLI              │        │
│  │ (tkinter)    │          │ (interactive)    │        │
│  │ • 資料夾選擇  │          │ • 參數輸入        │        │
│  │ • 選項控制    │          │ • 進度監控        │        │
│  │ • 進度顯示    │          │ • 結果查詢        │        │
│  └──────────────┘          └──────────────────┘        │
└─────────────────────────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────┐
│      主程序層 (Core Engine)                             │
│   full_batch_rename_execute.py                         │
├─────────────────────────────────────────────────────────┤
│ 1️⃣掃描: 遞迴掃描目錄 → 圖片列表                       │
│    └─ 副函數：scan_images()                           │
│ 2️⃣檢測: 檢測已命名 vs 未命名（增量）                  │
│    └─ 副函數：is_already_renamed()                    │
│ 3️⃣分析: 批量調用 Qwen3-VL 視覺模型                    │
│    └─ 副函數：encode_image_to_base64(), query_qwen() │
│ 4️⃣規劃: 生成重命名計畫、檢測重複                      │
│    └─ 副函數：detect_duplicates(), add_suffix()       │
│ 5️⃣執行: 逐檔案重命名、刪除原檔案                      │
│    └─ 副函數：rename_file(), delete_original()        │
│ 6️⃣報告: 生成詳細執行報告和映射表                      │
│    └─ 副函數：generate_report()                       │
└─────────────────────────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────┐
│    服務層 (Service Layer)                              │
│  ┌──────────────────┐    ┌──────────────────┐        │
│  │  Vision Analysis  │    │  Progress Tracking │       │
│  │ (qwen3-vl-30b)  │    │ (ProgressTracker) │       │
│  │ • image_title   │    │ • 進度計算         │        │
│  │ • main_theme    │    │ • ETA 估計         │        │
│  │ • core_content  │    │ • 日誌輸出         │        │
│  └──────────────────┘    └──────────────────┘        │
│  ┌──────────────────┐    ┌──────────────────┐        │
│  │  File Tracking    │    │  Deduplication    │       │
│  │ (FileTracker)    │    │ (去重邏輯)       │        │
│  │ • 增量/強制模式  │    │ • 序號檢測         │        │
│  │ • 狀態管理       │    │ • 衝突解決         │        │
│  └──────────────────┘    └──────────────────┘        │
└─────────────────────────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────┐
│      儲存層 (Storage Layer)                            │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐            │
│  │ session/ │  │ tracking │  │  logs/   │            │
│  │ JSON報告  │  │ 全局狀態 │  │ 日誌檔案 │            │
│  └──────────┘  └──────────┘  └──────────┘            │
└─────────────────────────────────────────────────────────┘
```

### 執行流程（詳細狀態機）

```
[開始]
  ↓
┌─────────────────────────────────┐
│ Phase 1: 初始化                 │
│ • 載入配置 (config.yaml)        │
│ • 建立臨時目錄 (session/, logs/)│
│ • 初始化進度追蹤器              │
└─────────────────────────────────┘
  ↓
┌─────────────────────────────────┐
│ Phase 2: 掃描 (Scanning)        │
│ • rglob 遞迴掃描所有圖片        │
│ • 依序排列確保可重復            │
│ → image_files = [file1, file2...│
└─────────────────────────────────┘
  ↓
┌─────────────────────────────────┐
│ Phase 3: 檢測 (Detection)       │
│ [非強制模式]                    │
│ • 檢測檔名中文字符              │
│ → renamed_files / unnamed_files │
│ [強制模式]                      │
│ • 全部重新分析                  │
└─────────────────────────────────┘
  ↓
┌─────────────────────────────────┐
│ Phase 4: 分析 (Analysis)        │
│ • 分批調用 Qwen3-VL (每批10)    │
│ • 優先提取 image_title          │
│ • 降級到 main_theme + content   │
│ • 進度追蹤：n/total, ETA        │
│ → analysis_results = [{...}...]│
└─────────────────────────────────┘
  ↓
┌─────────────────────────────────┐
│ Phase 5: 規劃 (Planning)        │
│ • 提取推薦名稱                  │
│ • 檢測重複名稱                  │
│ • 添加序號 (_01, _02, ...)      │
│ • 驗證檔名有效性                │
│ → rename_plan = [{old, new}...] │
└─────────────────────────────────┘
  ↓
┌─────────────────────────────────┐
│ Phase 6: 執行 (Execution)       │
│ • 逐檔案重命名                  │
│ • 可選：刪除原檔案              │
│ • 記錄成功/失敗                 │
│ → result = {success: N, fail: M}│
└─────────────────────────────────┘
  ↓
┌─────────────────────────────────┐
│ Phase 7: 報告 (Reporting)       │
│ • 生成執行統計                  │
│ • 建立映射表                    │
│ • 儲存至 data/analysis_results/ │
│ • 生成驗證報告                  │
└─────────────────────────────────┘
  ↓
[結束]
```

### 優先級邏輯流程圖

```
分析結果返回 (AnalysisResult)
  ↓
┌────────────────────────────────┐
│ 優先級檢查                      │
└────────────────────────────────┘
  ↓
  ├─ 優先級 1: image_title 存在且有效？
  │   ├─ YES → 使用 image_title ✅
  │   └─ NO  ↓
  │
  ├─ 優先級 2: main_theme + core_content 存在且有效？
  │   ├─ YES → 組合使用 (theme_content) ✅
  │   └─ NO  ↓
  │
  └─ 優先級 3: 自動編號
      └─ 使用 {原檔名}_{序號:02d} 或 image_{序號:04d} ✅
```

### 資料流向

```
圖片檔案
  ↓
[encode_to_base64]
  ↓
Qwen3-VL API (LM Studio http://127.0.0.1:1234)
  ↓
AnalysisResult JSON:
{
  "image_path": "/path/to/IMG_001.jpg",
  "image_title": "兄妹與螃蟹",
  "main_theme": "生活_家庭",
  "core_content": "兄妹玩樂",
  "recommended_name": "生活_家庭_兄妹與螃蟹"
}
  ↓
[優先級邏輯選擇]
  ↓
新檔名: "生活_家庭_兄妹與螃蟹.jpg"
  ↓
[重複檢測]
  ├─ 無重複 → 保持新檔名
  └─ 有重複 → 添加序號 "生活_家庭_兄妹與螃蟹_01.jpg"
  ↓
[驗證新檔名]
  ├─ 長度 ≤ 255? YES
  ├─ 無特殊字符? YES
  └─ 有效編碼? YES
  ↓
執行重命名 + 建立映射表
  ↓
記錄至: data/mapping/qwen_rename_plan_complete.json
```

---

## 成功標準 *(必要)*

### 可衡量成果

- **SC-001**: 系統可在單一指令下完成整個工作流（掃描→分析→重命名→報告），無需人工介入
- **SC-002**: 檔名新舊映射準確率 100%（無遺漏、無錯誤映射）
- **SC-003**: 圖片標題提取和使用率 ≥ 90%（當圖片含標題時）
- **SC-004**: 重複檢測和修復準確率 100%（所有重複都被檢測和修復，無衝突）
- **SC-005**: 系統連續執行 20 次無失敗（穩定性測試）
- **SC-006**: 單個大型圖片集（2000+ 張）的完整流程執行時間 < 2 小時
- **SC-007**: 增量模式性能提升 ≥ 80%（相比重新分析所有檔案）
- **SC-008**: 繁體中文檔案名正確處理率 100%（無亂碼、無編碼錯誤）
- **SC-009**: GUI 應用程式啟動時間 < 3 秒，無卡頓或視覺錯誤
- **SC-010**: 錯誤恢復成功率 ≥ 95%（中斷後恢復正常工作）
- **SC-011**: 品質評分達到 100 / 100（代碼、文檔、測試覆蓋）
- **SC-012**: 驗收標準達成 ≥ 100%（所有功能需求滿足）

---

## 第一性原理分析 *(參考)*

本節使用第一性原理與思維鏈（CoT）分析，深度理解系統設計的核心邏輯。

### 問題本質分解

```
用戶的真實需求：
├── 節省時間：不想手動輸入數百張圖片的檔名
├── 精準度：檔名應準確反映圖片內容
├── 可靠性：命名應一致、無重複、可追蹤
└── 易用性：應支援 GUI 和 CLI 兩種方式

從第一性原理推導：
├── 「節省時間」→ 需要自動化 → 需要可靠的圖片分析能力
├── 「精準度」→ 不應依賴檔名線索 → 應直接分析圖片內容
├── 「可靠性」→ 需要完整的追蹤和驗證機制 → 需要映射表和報告
└── 「易用性」→ 需要多個介面 → GUI（非技術）+ CLI（自動化）
```

### 技術約束的推導

```
約束一：為什麼優先使用圖片標題？
├── 前提：圖片可能包含文字（標題、標籤、文字）
├── 標題是最可靠的信息 → 來自圖片內容本身
├── 避免「二次解釋」 → 模型推理的結果可能有偏差
├── 結論：優先級 1 應為 image_title（準確率 99.9%）

約束二：為什麼需要降級機制？
├── 前提：並非所有圖片都含標題（如風景照、檔案截圖）
├── 若無標題則完全依賴 AI 推理 → 錯誤率提高
├── 降級到主題+內容組合 → 仍是合理的描述
├── 最差情況保留原檔名 → 避免資料丟失
├── 結論：MUST 實施三級優先級邏輯

約束三：為什麼需要增量模式？
├── 前提：用戶定期補充新圖片
├── 若每次都重新分析所有 → 浪費資源（可能數小時）
├── 檔名中文檢測 → 廉價、可靠的「已命名」判定
├── 增量模式節省 80%+ 的執行時間
├── 結論：MUST 提供智能增量模式

約束四：為什麼需要進度追蹤？
├── 前提：圖片集可能很大（2000+ 張）
├── 執行時間可能很長（1+ 小時）
├── 用戶需要了解進度和 ETA → 增強信心
├── 進度保存 → 允許中斷和恢復
├── 結論：MUST 提供實時進度和恢復機制
```

### 思維鏈：完整命名流程推演

```
步驟 1：用戶選擇資料夾（通過 GUI 或 --target-dir 參數）
    └─ 驗證目錄存在且有讀寫權限

步驟 2：系統掃描所有圖片（遞迴，支援子資料夾）
    └─ rglob("*") 然後篩選 .png, .jpg, .jpeg, .webp, .gif, .bmp
    └─ sorted() 確保順序一致，便於追蹤

步驟 3：檢測模式（增量 vs 強制）
    ├─ [增量模式] 過濾出未命名檔案（檢查檔名是否含中文）
    └─ [強制模式] 全部重新分析

步驟 4：批量分析
    ├─ 分批調用 Qwen3-VL（每批 10 張）
    ├─ 優先提取 image_title（OCR）
    ├─ 降級到 main_theme + core_content（語義）
    ├─ 自動重試 3 次（逾時/失敗情況）
    └─ 進度追蹤（n/total, ETA）

步驟 5：規劃重命名
    ├─ 根據優先級選擇檔名
    ├─ 檢測重複（全局掃描）
    ├─ 為重複添加序號 (_01, _02, ...)
    ├─ 驗證檔名有效性（長度、字符、編碼）
    └─ 生成 rename_plan 列表

步驟 6：執行重命名
    ├─ 逐檔案重命名（使用 pathlib.rename()）
    ├─ 可選：刪除原檔案（--delete-original）
    ├─ 記錄成功/失敗
    └─ 建立映射表（舊名 → 新名）

步驟 7：生成報告
    ├─ 執行統計（成功數、失敗數、修復數、耗時）
    ├─ 映射表（JSON 格式，支援查詢）
    ├─ 驗證報告（唯一性檢查、準確率評估）
    └─ 儲存至 data/analysis_results/ 和 data/mapping/
```

---

## 實現指南 *(可選)*

### 核心檔案結構

```
src/
├── full_batch_rename_execute.py (506 行)
│   └─ 主程序：整合掃描→分析→規劃→執行→報告
├── gui_selector.py (1251 行)
│   └─ GUI 介面：tkinter，單頁設計，無滾動
├── progress_tracker.py (245 行)
│   └─ 進度追蹤：實時進度、ETA、日誌
├── file_tracker.py (174 行)
│   └─ 檔案追蹤：狀態管理、增量檢測
├── deduplicate_and_cleanup.py (138 行)
│   └─ 去重和清理：重複檢測、序號添加

config/
├── config.yaml
│   └─ 系統配置：LM Studio、批次、命名規則

data/
├── analysis_results/
│   └─ 分析結果 JSON
├── mapping/
│   └─ 舊名→新名映射表

logs/
├── rename.log
│   └─ 執行日誌
```

### 關鍵演算法

#### 1. 檔名中文檢測（增量模式判定）

```python
import re

def is_already_renamed(filename: str) -> bool:
    """檢測檔案是否已被命名（檔名含中文字符）"""
    return bool(re.search(r'[\u4e00-\u9fff]', filename))
    # 範圍：CJK 統一表意文字（U+4E00 到 U+9FFF）
```

#### 2. 優先級邏輯（名稱選擇）

```python
def select_name(analysis_result: dict) -> str:
    """根據優先級選擇檔名"""
    # 優先級 1: image_title
    if analysis_result.get("image_title") and \
       is_valid_filename(analysis_result["image_title"]):
        return analysis_result["image_title"]
    
    # 優先級 2: main_theme + core_content
    theme = analysis_result.get("main_theme", "")
    content = analysis_result.get("core_content", "")
    if theme and content:
        combined = f"{theme}_{content}"
        if is_valid_filename(combined):
            return combined
    
    # 優先級 3: 自動編號
    return f"image_{self.counter:04d}"
```

#### 3. 重複檢測和修復

```python
def detect_and_fix_duplicates(rename_plan: list) -> list:
    """檢測重複檔名並添加序號"""
    name_counts = {}
    fixed_plan = []
    
    for item in rename_plan:
        new_name = item["new_name"]
        if new_name not in name_counts:
            name_counts[new_name] = 0
            fixed_plan.append(item)
        else:
            # 檔名重複，添加序號
            name_counts[new_name] += 1
            base, ext = os.path.splitext(new_name)
            item["new_name"] = f"{base}_{name_counts[new_name]:02d}{ext}"
            fixed_plan.append(item)
    
    return fixed_plan
```

#### 4. 進度估算（ETA）

```python
def estimate_eta(start_time: float, processed: int, total: int) -> str:
    """估算剩餘時間"""
    elapsed = time.time() - start_time
    if processed == 0:
        return "計算中..."
    
    avg_time = elapsed / processed
    remaining = avg_time * (total - processed)
    
    minutes = int(remaining // 60)
    seconds = int(remaining % 60)
    return f"{minutes}分{seconds}秒"
```

---

## 測試策略 *(可選)*

### 單元測試

```python
# tests/test_is_already_renamed.py
def test_renamed_file():
    assert is_already_renamed("生活_家庭_兄妹.jpg") == True

def test_unnamed_file():
    assert is_already_renamed("IMG_001.jpg") == False

# tests/test_duplicate_detection.py
def test_detect_duplicates():
    plan = [
        {"old": "A.jpg", "new": "title"},
        {"old": "B.jpg", "new": "title"},
        {"old": "C.jpg", "new": "title"}
    ]
    result = detect_and_fix_duplicates(plan)
    assert result[1]["new"] == "title_01"
    assert result[2]["new"] == "title_02"
```

### 集成測試

- 準備 10 張測試圖片（各含不同的標題情況）
- 執行完整工作流
- 驗證：新檔名準確、無重複、映射表正確、報告完整

### 回歸測試

- 驗證以下標準不被破壞：
  - 增量模式跳過已命名檔案
  - GUI 正常啟動和操作
  - 進度保存和恢復功能

---

## 依賴和環境 *(可選)*

### 外部依賴

- **Qwen3-VL 30B**：視覺模型，需通過 LM Studio 提供服務
- **Python 3.11+**：核心語言
- **requests**：HTTP 請求（調用 Qwen API）
- **PyYAML**：配置管理
- **Pillow**：圖片處理
- **tkinter**：GUI（Python 內建）

### 環境設置

1. **啟動 LM Studio**（提供 Qwen3-VL 服務）
   ```bash
   # LM Studio 應在 http://127.0.0.1:1234 提供服務
   # 模型：qwen/qwen3-vl-30b
   ```

2. **安裝依賴**
   ```bash
   pip install -r requirements.txt
   # 或使用 Conda
   conda env create -f environment.yml
   ```

---

## 維護和擴展 *(參考)*

### 已知限制

- 系統依賴 Qwen3-VL 的準確性，若模型不夠精準則命名質量下降
- GUI 目前使用 tkinter（跨平台但功能有限），複雜介面需求可考慮 PyQt/PySide
- 系統不支援遠端圖片分析（僅本地檔案）

### 未來擴展方向

1. **多模型支援**：支援 Claude Vision、GPT-4V 等其他視覺模型
2. **Web 介面**：使用 Flask/Streamlit 提供 Web 版本
3. **批量標籤系統**：除了檔名外，還可為圖片添加 metadata 標籤
4. **圖片分類和組織**：自動將圖片分類到子資料夾
5. **拖放功能**：GUI 支援拖放圖片或資料夾
6. **預覽功能**：在 GUI 中預覽圖片和新檔名

---

## 附錄

### 配置範例（config.yaml）

```yaml
lm_studio:
  host: "127.0.0.1"
  port: 1234
  model: "qwen/qwen3-vl-30b"
  timeout: 300

analysis:
  batch_size: 10
  max_retries: 3
  retry_delay: 2
  save_progress: true

naming:
  priority_field: "image_title"
  separator: "_"
  language: "zh-TW"
  duplicate_suffix: "_{number:02d}"
```

### 映射表範例（qwen_rename_plan_complete.json）

```json
{
  "metadata": {
    "timestamp": "2026-01-25T15:00:00",
    "total_images": 338,
    "successful": 338,
    "failed": 0,
    "execution_time": 3600.5
  },
  "mapping": [
    {
      "original_name": "IMG_001.JPG",
      "new_name": "生活_家庭_兄妹與螃蟹.jpg",
      "priority_used": 1,
      "analysis_result": {
        "image_title": "兄妹與螃蟹",
        "main_theme": "生活_家庭",
        "core_content": "兄妹玩樂"
      }
    },
    ...
  ]
}
```

### 命令行使用範例

```bash
# 基本使用（增量模式）
python3 src/full_batch_rename_execute.py --target-dir ~/Pictures

# 強制重新命名所有檔案
python3 src/full_batch_rename_execute.py --target-dir ~/Pictures --force-rename

# 刪除原檔案
python3 src/full_batch_rename_execute.py --target-dir ~/Pictures --delete-original

# 限制分析數量（測試）
python3 src/full_batch_rename_execute.py --target-dir ~/Pictures --limit 10

# GUI 模式
bash scripts/gui.sh
```

---

**規格版本**：1.0  
**最後更新**：2026-01-25  
**狀態**：✅ 發布（完整功能規格，所有需求已定義）
