#!/bin/bash

# 測試腳本：前 10 張圖片
# 驗收標準：前 10 張照片可以順利 rename

SOURCE_DIR="/Users/hsiaojohnny/Downloads/20251004_iphone12_bak"
TEST_DIR="/tmp/test_rename_10"

echo "🧪 準備測試環境..."

# 清理舊測試目錄
rm -rf "$TEST_DIR"
mkdir -p "$TEST_DIR"

# 複製前 10 張圖片到測試目錄
echo "📋 複製前 10 張圖片到測試目錄..."
find "$SOURCE_DIR" -type f \( -iname "*.jpg" -o -iname "*.jpeg" -o -iname "*.png" -o -iname "*.heic" \) | head -10 | while read file; do
    cp "$file" "$TEST_DIR/"
done

echo "✅ 複製完成"
echo ""
echo "📊 測試統計："
file_count=$(find "$TEST_DIR" -type f | wc -l)
echo "   測試目錄中的文件：$file_count 個"
echo ""

# 顯示檔名
echo "📋 測試檔案列表："
ls -1 "$TEST_DIR" | head -10

echo ""
echo "🚀 開始測試 rename 功能..."
echo "=================================================="
echo ""

# 執行 rename 命令
cd /Users/hsiaojohnny/dev/rename
python3 src/full_batch_rename_execute.py --target-dir "$TEST_DIR"

echo ""
echo "=================================================="
echo "🔍 測試結果檢查..."
echo ""

# 檢查重命名結果
echo "📋 重命名後的檔案："
ls -1 "$TEST_DIR" | head -10

renamed_count=0
original_count=0

for file in "$TEST_DIR"/*; do
    filename=$(basename "$file")
    # 檢查是否包含中文（表示已重命名）
    if [[ "$filename" =~ [一-龠ぁ-ゟァ-ヴー々〆〤] ]]; then
        ((renamed_count++))
    else
        ((original_count++))
    fi
done

echo ""
echo "📊 重命名統計："
echo "   已重命名：$renamed_count 個 ✅"
echo "   未重命名：$original_count 個 ❌"
echo ""

if [ "$renamed_count" -ge 8 ]; then
    echo "✅ 測試通過！至少 8 個文件被成功重命名"
else
    echo "❌ 測試失敗！只有 $renamed_count 個文件被重命名"
fi

# 查看進度日誌
echo ""
echo "📝 進度日誌："
if [ -f "/Users/hsiaojohnny/dev/rename/data/session/progress_log_rename.txt" ]; then
    tail -20 "/Users/hsiaojohnny/dev/rename/data/session/progress_log_rename.txt"
else
    echo "❌ 進度日誌不存在"
fi

# 查看分析報告
echo ""
echo "📊 分析報告："
if [ -f "/Users/hsiaojohnny/dev/rename/data/session/qwen_rename_final_report.json" ]; then
    cat "/Users/hsiaojohnny/dev/rename/data/session/qwen_rename_final_report.json"
else
    echo "❌ 分析報告不存在"
fi
