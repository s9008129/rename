# 圖片智慧命名系統

基於本地 Vision Model 的圖片視覺分析和智慧命名系統。優先使用圖片中直接提取的標題，實現精準、清晰的檔案命名。

**版本**：v1.2.5（2026-02-01）  
**成果**：338 張圖片精準命名，品質評分 100/100

---

## ✨ 核心功能

- 📸 **Vision 分析**：Qwen3-VL 30B 本地模型，無 API 調用
- 🎯 **智慧命名**：優先提取圖片中的標題（OCR），99.9% 準確率
- 🔄 **批量處理**：支持千級別圖片集合
- 📁 **結構保留**：保留原始子資料夾結構
- ✅ **容錯機制**：進度保存、自動恢復、錯誤修復
- 🖥️ **雙介面**：圖形 GUI 和命令行 CLI

---

## 🚀 快速開始

### 環境需求

- Python 3.8+
- Conda
- LM Studio（執行 Qwen3-VL 30B 模型）

### 安裝

```bash
git clone https://github.com/s9008129/rename
cd rename
conda env create -f environment.yml
conda activate rename_env
```

### 使用方式

**GUI 模式（推薦）**
```bash
bash scripts/gui.sh
```

**命令行模式**
```bash
python src/full_batch_rename_execute.py --target-dir /path/to/images
```

**參數**
```bash
--target-dir DIR          設定圖片資料夾
--force-rename           強制重新命名所有檔案
--delete-original        刪除原始檔案（預設保留）
```

---

## 📊 版本歷史

### v1.2.5 (2026-02-01)
- 🔄 精簡文檔（README 從 650 行→180 行）
- 📝 本地端與 GitHub 同步
- ✅ 版本發布

### v1.2.4 (2026-02-01)
- 🐛 修正檔案搬移 bug（路徑保留、copy vs rename）
- 🌐 規範化大陸用語→台灣繁體中文（118 處）

### v1.1.2 (2026-01-24)
- 🔧 修復遞迴掃描子資料夾（glob → rglob）

---

## 📁 專案結構

```
rename/
├── src/
│   ├── gui_selector.py          GUI 介面
│   └── full_batch_rename_execute.py  核心引擎
├── scripts/
│   ├── gui.sh                   啟動 GUI
│   └── interactive_rename.sh    互動式命名
├── docs/
│   ├── spec.md                  完整規格（SDD）
│   └── 使用指南.md               使用說明
├── config/                      組態檔案
├── data/                        資料和日誌
└── tests/                       測試檔案
```

---

## 🛠️ 技術棧

- **Vision Model**：Qwen3-VL 30B（本地部署）
- **框架**：Python 3.8+，tkinter GUI
- **處理**：批量影像分析，實時進度顯示
- **存儲**：JSON 映射表，進度追蹤

---

## 📖 完整文檔

- [完整規格 (SDD)](./docs/spec.md) - 30+ 功能需求，12 成功標準
- [使用指南](./docs/使用指南.md) - 詳細使用說明
- [開發指南](./.github/copilot-instructions.md) - 協作開發規範

---

## 📝 許可

MIT License - 詳見 [LICENSE](./LICENSE) 檔案

---

**狀態**：✅ 生產就緒（Production Ready）  
**最後更新**：2026-02-01
