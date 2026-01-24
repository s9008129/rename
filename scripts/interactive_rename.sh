#!/bin/bash

#######################################################
# 🎯 圖片智能命名系統 - 互動式介面 (v1.1)
# 功能：
#   • 讓用戶指定資料夾並選擇是否刪除原檔案
#   • 智能檢測已命名 vs 未命名檔案
#   • 支援增量模式（默認）和強制重新命名模式
# 最小成本、輕量化設計
#######################################################

set -e

# 檢查命令行參數
FORCE_RENAME=false
for arg in "$@"; do
    if [ "$arg" = "--force-rename" ] || [ "$arg" = "--override" ]; then
        FORCE_RENAME=true
    fi
done

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

# 項目設定
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CONDA_ENV="image-rename"
CONFIG_FILE="${PROJECT_ROOT}/config/config.yaml"
LOG_DIR="${PROJECT_ROOT}/logs"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
LOG_FILE="${LOG_DIR}/run_${TIMESTAMP}.log"

# 創建日誌目錄
mkdir -p "$LOG_DIR"

#######################################################
# 🔧 工具函數
#######################################################

print_header() {
    echo -e "\n${BLUE}${BOLD}═══════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}${BOLD}$1${NC}"
    echo -e "${BLUE}${BOLD}═══════════════════════════════════════════════════════${NC}\n"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "${CYAN}ℹ️  $1${NC}"
}

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# 詢問用戶 Yes/No
ask_yes_no() {
    local prompt="$1"
    local default="$2"  # "y" 或 "n"
    local response
    
    while true; do
        echo -en "${BOLD}$prompt${NC} "
        if [ -n "$default" ]; then
            if [ "$default" = "y" ]; then
                echo -en "(Y/n): "
            else
                echo -en "(y/N): "
            fi
        else
            echo -en "(y/n): "
        fi
        
        read -r response
        response=$(echo "$response" | tr '[:upper:]' '[:lower:]')
        
        if [ -z "$response" ] && [ -n "$default" ]; then
            response="$default"
        fi
        
        case "$response" in
            y|yes) return 0 ;;
            n|no)  return 1 ;;
            *)     print_warning "請輸入 y 或 n" ;;
        esac
    done
}

# 詢問用戶路徑
ask_directory() {
    local prompt="$1"
    local directory
    
    while true; do
        echo -e "${BOLD}$prompt${NC}"
        read -r directory
        
        # 展開 ~ 符號
        directory="${directory/#\~/$HOME}"
        
        # 檢查是否存在
        if [ ! -d "$directory" ]; then
            print_error "目錄不存在：$directory"
            continue
        fi
        
        echo "$directory"
        return 0
    done
}

# 計算圖片數量
count_images() {
    local dir="$1"
    find "$dir" -maxdepth 1 \( -iname "*.jpg" -o -iname "*.jpeg" -o -iname "*.png" \
        -o -iname "*.gif" -o -iname "*.webp" -o -iname "*.bmp" \) -type f 2>/dev/null | wc -l
}

# 智能檢測已命名檔案（新增）
detect_renamed_files() {
    local dir="$1"
    local has_chinese=0
    local unnamed_count=0
    local renamed_count=0
    
    # 統計包含中文和不包含中文的檔案
    while IFS= read -r -d '' file; do
        filename=$(basename "$file")
        # 簡單的中文檢測：通過 grep 或 perl
        if echo "$filename" | grep -q '[^\x00-\x7F]'; then
            ((renamed_count++))
        else
            ((unnamed_count++))
        fi
    done < <(find "$dir" -maxdepth 1 \( -iname "*.jpg" -o -iname "*.jpeg" -o -iname "*.png" \
        -o -iname "*.gif" -o -iname "*.webp" -o -iname "*.bmp" \) -type f -print0 2>/dev/null)
    
    echo "$unnamed_count $renamed_count"
}

#######################################################
# 📋 主程序流程
#######################################################

main() {
    clear
    
    # 顯示歡迎信息
    print_header "🎯 圖片智能命名系統 v1.1"
    
    echo -e "歡迎使用互動式圖片命名工具！"
    echo -e ""
    echo -e "此工具可以幫助你："
    echo -e "  • 掃描指定資料夾中的圖片"
    echo -e "  • 智能檢測已命名 vs 未命名的檔案"
    echo -e "  • 使用 AI 進行視覺分析"
    echo -e "  • 自動生成精準的中文命名"
    echo -e "  • 選擇是否刪除原檔案"
    echo -e ""
    
    if [ "$FORCE_RENAME" = true ]; then
        print_warning "⚠️  強制重新命名模式已啟用（--force-rename）"
        echo ""
    fi
    
    # 第一步：詢問圖片資料夾
    print_info "步驟 1: 選擇要命名的資料夾"
    echo ""
    IMAGE_DIR=$(ask_directory "請輸入圖片資料夾的路徑 (或按 Enter 使用 ~/Downloads):")
    
    if [ -z "$IMAGE_DIR" ]; then
        IMAGE_DIR="$HOME/Downloads"
    fi
    
    # 驗證圖片數量和檢測已命名檔案
    IMAGE_COUNT=$(count_images "$IMAGE_DIR")
    
    if [ "$IMAGE_COUNT" -eq 0 ]; then
        print_warning "找不到圖片檔案"
        echo -e "${BOLD}是否繼續？(y/n): ${NC}"
        if ! ask_yes_no "繼續？" "n"; then
            print_warning "操作已取消"
            exit 0
        fi
    else
        print_success "找到 $IMAGE_COUNT 個圖片檔案"
        
        # 智能檢測已命名的檔案
        read UNNAMED_COUNT RENAMED_COUNT <<< "$(detect_renamed_files "$IMAGE_DIR")"
        
        if [ "$RENAMED_COUNT" -gt 0 ]; then
            echo ""
            print_warning "檢測到 $RENAMED_COUNT 個已命名的檔案，$UNNAMED_COUNT 個未命名的檔案"
            
            if [ "$FORCE_RENAME" = false ]; then
                print_info "📌 增量模式（默認）：將只命名 $UNNAMED_COUNT 個未命名的檔案"
                print_info "💡 提示：如果想重新命名所有檔案，使用 --force-rename 參數"
            else
                print_warning "📌 強制模式：將重新命名全部 $IMAGE_COUNT 個檔案（包括已命名的）"
            fi
        fi
    fi
    
    echo ""
    print_info "📍 圖片資料夾：$IMAGE_DIR"
    echo ""
    
    # 第二步：詢問是否刪除原檔案
    print_info "步驟 2: 選擇是否刪除原檔案"
    echo ""
    echo -e "重命名後，是否刪除原檔案？"
    echo -e "  • 選 ${GREEN}是${NC} - 刪除原檔案，只保留新命名的檔案"
    echo -e "  • 選 ${GREEN}否${NC} - 保留原檔案（推薦，更安全）"
    echo ""
    
    DELETE_ORIGINAL=false
    if ask_yes_no "是否刪除原檔案？" "n"; then
        DELETE_ORIGINAL=true
        print_warning "⚠️  確認：重命名後將刪除原檔案"
        echo ""
        
        # 二次確認
        if ! ask_yes_no "確定要刪除原檔案嗎？這個操作無法撤銷！" "n"; then
            DELETE_ORIGINAL=false
            print_info "已取消刪除原檔案選項"
        fi
    else
        print_success "將保留原檔案（推薦）"
    fi
    
    echo ""
    
    # 第三步：確認設定
    print_info "步驟 3: 確認設定"
    echo ""
    echo -e "${BOLD}任務設定摘要：${NC}"
    echo -e "  • 圖片資料夾：$IMAGE_DIR"
    echo -e "  • 圖片數量：$IMAGE_COUNT 個"
    echo -e "  • 刪除原檔案：$([ "$DELETE_ORIGINAL" = true ] && echo '是' || echo '否')"
    echo ""
    
    if ! ask_yes_no "確認開始處理嗎？" "y"; then
        print_warning "操作已取消"
        exit 0
    fi
    
    # 環境檢查
    echo ""
    print_info "步驟 4: 環境檢查"
    echo ""
    
    # 檢查 Conda
    if ! command -v conda &> /dev/null; then
        print_error "找不到 Conda"
        exit 1
    fi
    print_success "Conda 已安裝"
    
    # 檢查/創建環境
    if ! conda env list | grep -q "^${CONDA_ENV} "; then
        print_warning "環境 '${CONDA_ENV}' 不存在，正在創建..."
        if conda env create -f "${PROJECT_ROOT}/environment.yml" -q; then
            print_success "環境創建成功"
        else
            print_error "環境創建失敗"
            exit 1
        fi
    else
        print_success "環境 '${CONDA_ENV}' 已存在"
    fi
    
    # 檢查 LM Studio
    if ! timeout 2 curl -s http://127.0.0.1:1234/v1/models > /dev/null 2>&1; then
        print_error "LM Studio 未運行 (127.0.0.1:1234)"
        echo -e "${YELLOW}請先打開 LM Studio 並加載 qwen3-vl-30b${NC}"
        exit 1
    fi
    print_success "LM Studio 已連接"
    
    echo ""
    
    # 執行分析
    print_header "🚀 開始分析和重命名"
    echo -e "${YELLOW}⏱️  這可能需要幾分鐘，請耐心等待...${NC}\n"
    
    log "=========================================="
    log "開始執行圖片重命名流程"
    log "圖片資料夾：$IMAGE_DIR"
    log "刪除原檔案：$([ "$DELETE_ORIGINAL" = true ] && echo '是' || echo '否')"
    log "=========================================="
    
    # 執行分析腳本
    PYTHON_ARGS=("--target-dir" "$IMAGE_DIR")
    if [ "$FORCE_RENAME" = true ]; then
        PYTHON_ARGS+=("--force-rename")
    fi
    
    if conda run -n "$CONDA_ENV" python "${PROJECT_ROOT}/src/full_batch_rename_execute.py" \
        "${PYTHON_ARGS[@]}"; then
        
        echo ""
        print_header "✨ 分析完成！"
        
        # 如果選擇刪除原檔案
        if [ "$DELETE_ORIGINAL" = true ]; then
            print_warning "處理原檔案..."
            
            # 計算需要刪除的檔案
            DELETE_COUNT=0
            
            # 尋找所有原始檔案（copilot-image-* 格式）並刪除
            while IFS= read -r -d '' file; do
                rm -f "$file"
                ((DELETE_COUNT++))
                log "已刪除：$file"
            done < <(find "$IMAGE_DIR" -maxdepth 1 -iname "copilot-image-*.png" -o -iname "copilot-image-*.jpg" -o -iname "copilot-image-*.jpeg" -print0 2>/dev/null)
            
            if [ "$DELETE_COUNT" -gt 0 ]; then
                print_success "已刪除 $DELETE_COUNT 個原檔案"
                log "已刪除 $DELETE_COUNT 個原檔案"
            fi
        else
            print_success "已保留原檔案"
            log "已保留原檔案"
        fi
        
        echo ""
        print_success "圖片重命名完成！"
        print_info "日誌文件：$LOG_FILE"
        print_info "圖片目錄：$IMAGE_DIR"
        
        log "=========================================="
        log "圖片重命名流程完成"
        log "=========================================="
        
        # 詢問是否打開目錄
        echo ""
        if ask_yes_no "是否打開圖片目錄查看結果？" "y"; then
            if [ "$(uname)" = "Darwin" ]; then
                open "$IMAGE_DIR"
            elif [ "$(uname)" = "Linux" ]; then
                xdg-open "$IMAGE_DIR" 2>/dev/null || nautilus "$IMAGE_DIR" 2>/dev/null || echo "請手動打開：$IMAGE_DIR"
            fi
        fi
        
    else
        echo ""
        print_error "圖片分析失敗"
        log "圖片分析失敗"
        echo ""
        echo -e "${YELLOW}建議：${NC}"
        echo "1. 檢查 LM Studio 是否正在運行"
        echo "2. 檢查網絡連接"
        echo "3. 查看詳細日誌：$LOG_FILE"
        exit 1
    fi
}

# 捕捉 Ctrl+C
trap 'echo ""; print_warning "操作已中止"; log "使用者中止操作"; exit 130' INT

# 運行主程序
main
