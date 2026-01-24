# 🎯 一鍵執行指南 - 給非技術人員的使用說明

## 📌 簡介

本指南幫助非技術人員快速完成圖片重新命名。無需了解任何技術概念，只需運行一個命令即可。

---

## ⚡ 快速開始（5 分鐘）

### 第一次使用（一次性設置）

#### 1️⃣ 檢查系統要求
確保你已經安裝：
- **Miniconda 或 Anaconda** - Python 環境管理工具
  - 下載：https://docs.conda.io/projects/miniconda/en/latest/
  - 安裝後重啟終端

- **LM Studio** - 本地 AI 模型運行工具  
  - 下載：https://lmstudio.ai/
  - 安裝完後需要：
    1. 打開 LM Studio
    2. 搜索並加載模型「qwen/qwen3-vl-30b」（約 35GB，需要空間足夠）
    3. 點擊「Start Server」，確保顯示「Server running at 127.0.0.1:1234」

#### 2️⃣ 打開終端

**macOS 用戶：**
- 按 `Cmd + Space`，搜索「Terminal」，打開

**Windows 用戶：**
- 按 `Win + X`，選「Windows PowerShell」或「終端」

**Linux 用戶：**
- 右鍵點桌面或應用菜單打開終端

#### 3️⃣ 進入項目目錄

```bash
cd ~/Downloads/dev/rename
```

#### 4️⃣ 執行一鍵命令

**選項 A：簡化版（推薦非技術人員）**
```bash
bash scripts/quick_rename.sh
```

**選項 B：完整版（可自訂選項）**
```bash
bash scripts/run_image_rename.sh
```

---

## 📖 詳細步驟

### 使用「簡化版」腳本（推薦）

```bash
bash scripts/quick_rename.sh
```

**執行過程：**
1. ✓ 自動檢查 Conda 環境
2. ✓ 自動檢查 LM Studio 連接
3. ✓ 自動掃描 ~/Downloads 下的圖片
4. ✓ 自動分析和重新命名（可能需要 5-20 分鐘）
5. ✓ 自動打開資源管理器顯示結果

**成功標誌：**
```
╔════════════════════════════════════════╗
║  ✅ 圖片命名完成！                      ║
╚════════════════════════════════════════╝
```

### 使用「完整版」腳本（需要互動）

```bash
bash scripts/run_image_rename.sh
```

**特色：**
- ✓ 更詳細的進度提示
- ✓ 可選擇圖片目錄
- ✓ 詳細的日誌記錄
- ✓ 可對話式確認

**執行過程中會詢問：**
1. "是否繼續？" → 按 `y` 然後 Enter
2. "圖片目錄是否正確？" → 按 `y` 或輸入自定義路徑
3. "是否打開資源管理器查看結果？" → 按 `y` 查看結果

---

## ❌ 遇到問題？

### 問題 1：「找不到 Conda」

**解決方案：**
```bash
# 檢查是否已安裝
conda --version

# 如果無法識別，需要重啟終端或重新安裝 Miniconda
```

### 問題 2：「LM Studio 未運行」

**解決方案：**
1. 打開 LM Studio 應用
2. 搜索「qwen3-vl-30b」
3. 點擊 Download（首次會花 30-60 分鐘）
4. 加載完後點「Start Server」
5. 查看底部是否顯示「Server running on 127.0.0.1:1234」
6. 重新運行腳本

### 問題 3：「找不到圖片」

**解決方案：**
- 確保圖片在 `~/Downloads` 目錄中
- 支持的格式：`.jpg`, `.png`, `.gif`, `.webp`, `.bmp`
- 或在運行腳本時自訂目錄路徑

### 問題 4：「分析很慢或卡住」

**可能原因：**
1. LM Studio 正在加載模型（第一次會花很長時間）
2. 網絡不穩定
3. 電腦資源不足

**解決方案：**
- 耐心等待（可能需要 10-30 分鐘）
- 查看日誌文件瞭解詳細狀態：
```bash
tail -f ~/Downloads/dev/rename/logs/*.log
```

### 問題 5：「某些圖片沒有被重命名」

**可能原因：**
1. 圖片無法被模型處理（如 WebP 格式或損壞）
2. 圖片中沒有可識別的文字內容

**解決方案：**
- 這是正常的，系統會自動跳過無法處理的圖片
- 查看日誌瞭解跳過的原因

---

## 🔄 重複運行

### 如何再次運行？

```bash
# 進入項目目錄
cd ~/Downloads/dev/rename

# 執行腳本（和第一次一樣）
bash scripts/quick_rename.sh
```

### 如何只分析新增的圖片？

系統會自動檢測已重命名的文件並跳過，只分析新圖片。

### 如何清除日誌？

```bash
# 清除舊日誌（保留程式，只刪除日誌）
rm ~/Downloads/dev/rename/logs/*.log
```

---

## 📊 理解結果

### 重命名規則

命名格式：`[主題]_[標題]_[詳細描述].副檔名`

**例子：**
- `財經_投資分析_美股代號COIN.png`
- `AI技術_GPT-5.2-Codex_軟體工程典範移轉.png`
- `UI設計_暗色主題_表單元件庫設計.jpg`

### 生成的文件

- **~/Downloads/dev/rename/logs/run_YYYYMMDD_HHMMSS.log** - 詳細執行日誌
- **~/Downloads/dev/rename/data/mapping_YYYYMMDD_HHMMSS.json** - 映射表（舊名→新名）
- **~/Downloads/dev/rename/data/analysis_YYYYMMDD_HHMMSS.json** - 分析結果詳情

---

## 🎯 驗收標準

✅ **成功標誌：**
- 圖片被正確重命名
- 檔名包含有意義的中文描述
- 看到檔名就能聯想到圖片內容

❌ **失敗標誌：**
- 圖片名稱未改變
- 出現錯誤信息（紅色文字）
- 腳本中止或無法連接 LM Studio

---

## 💡 進階使用（技術人員）

### 自訂圖片目錄

```bash
# 完整版允許自訂
bash scripts/run_image_rename.sh
# 按提示輸入自訂目錄路徑

# 或直接修改腳本中的 IMAGE_DIR 變數
```

### 查看詳細日誌

```bash
# 查看最新日誌
cat ~/Downloads/dev/rename/logs/run_*.log | tail -100

# 監視日誌實時更新
tail -f ~/Downloads/dev/rename/logs/run_*.log
```

### 修改配置參數

編輯 `~/Downloads/dev/rename/config/config.yaml`：
```yaml
# LM Studio API 設置
lm_studio:
  host: 127.0.0.1
  port: 1234
  
# 命名規則
naming:
  priority_field: "image_title"  # 優先使用提取的圖片標題
  language: "zh-TW"               # 台灣繁體中文
```

---

## 📞 獲得幫助

如果遇到問題：

1. **查看日誌**
   ```bash
   cat ~/Downloads/dev/rename/logs/run_*.log
   ```

2. **檢查項目文檔**
   ```bash
   cat ~/Downloads/dev/rename/README.md
   ```

3. **檢查 Copilot 指導**
   ```bash
   cat ~/Downloads/dev/rename/.github/copilot-instructions.md
   ```

---

**最後更新：2026-01-24**  
**版本：1.0.0**  
**目標用戶：非技術人員**  
**難度等級：⭐ 極簡單**
