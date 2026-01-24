#!/bin/bash

# 圖片智能命名系統 - GUI 啟動腳本
# 用途：使用圖形介面選擇資料夾並執行命名

# 設置項目根目錄
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# 檢查 Python
if ! command -v python3 &> /dev/null; then
    echo "❌ 錯誤：找不到 Python 3"
    echo "請先安裝 Python 3.11 或更新版本"
    exit 1
fi

# 檢查 conda 環境
if [ -z "$CONDA_DEFAULT_ENV" ]; then
    echo "⚠️ 提示：您還未激活 conda 環境"
    echo "請先執行：conda activate image-rename"
    echo ""
    echo "自動激活環境..."
    eval "$(conda shell.bash hook)"
    conda activate image-rename 2>/dev/null || {
        echo "❌ 無法自動激活環境"
        exit 1
    }
fi

echo "🚀 啟動圖片智能命名系統 GUI..."
echo ""

# 運行 GUI
python3 "$PROJECT_ROOT/src/gui_selector.py"
