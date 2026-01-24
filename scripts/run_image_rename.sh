#!/bin/bash

#######################################################
# 🎯 圖片智能命名系統 - 一鍵執行腳本
# 目標：讓非技術人員一鍵完成圖片重新命名
# 驗收標準：清晰的進度、成功/失敗反饋、可恢復
#######################################################

set -e  # 任何錯誤立即停止

# 顏色定義（用於清晰的終端輸出）
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# 項目根路徑（自動偵測）
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CONDA_ENV="image-rename"
IMAGE_DIR="${PROJECT_ROOT}/data/images"  # 預設圖片目錄
CONFIG_FILE="${PROJECT_ROOT}/config/config.yaml"
LOG_DIR="${PROJECT_ROOT}/logs"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
LOG_FILE="${LOG_DIR}/run_${TIMESTAMP}.log"

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
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_step() {
    echo -e "\n${BOLD}📍 $1${NC}"
}

# 日誌記錄函數
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# 創建日誌目錄
mkdir -p "$LOG_DIR"

#######################################################
# 🔍 環境檢查函數
#######################################################

check_conda_installed() {
    print_step "檢查 Conda 環境..."
    
    if ! command -v conda &> /dev/null; then
        print_error "找不到 Conda！"
        echo ""
        echo "💡 請先安裝 Miniconda 或 Anaconda："
        echo "   https://docs.conda.io/projects/miniconda/en/latest/"
        exit 1
    fi
    
    print_success "Conda 已安裝"
    log "✓ Conda 已安裝"
}

check_conda_env_exists() {
    print_step "檢查 Conda 環境 '${CONDA_ENV}'..."
    
    # 檢查環境是否存在
    if ! conda env list | grep -q "^${CONDA_ENV} "; then
        print_warning "環境 '${CONDA_ENV}' 不存在，需要創建..."
        log "⚠  環境 '${CONDA_ENV}' 不存在，創建中..."
        
        echo -e "\n${BOLD}📦 創建 Conda 環境（約需 2-3 分鐘）...${NC}"
        if conda env create -f "${PROJECT_ROOT}/environment.yml" >> "$LOG_FILE" 2>&1; then
            print_success "環境創建成功"
            log "✓ 環境創建成功"
        else
            print_error "環境創建失敗"
            log "✗ 環境創建失敗，查看日誌：$LOG_FILE"
            exit 1
        fi
    else
        print_success "環境 '${CONDA_ENV}' 已存在"
        log "✓ 環境已存在"
    fi
}

check_lm_studio() {
    print_step "檢查 LM Studio 連接..."
    
    # 檢查 LM Studio 是否運行
    if timeout 3 curl -s http://127.0.0.1:1234/v1/models > /dev/null 2>&1; then
        print_success "LM Studio 已連接"
        log "✓ LM Studio 已連接"
        return 0
    else
        print_error "無法連接 LM Studio (127.0.0.1:1234)"
        echo ""
        echo "💡 請確保 LM Studio 正在運行："
        echo "   1. 打開 LM Studio 應用"
        echo "   2. 加載模型 'qwen/qwen3-vl-30b'"
        echo "   3. 開始本地伺服器（應該在 127.0.0.1:1234）"
        echo ""
        print_warning "是否繼續？(y/n): "
        read -r response
        if [ "$response" != "y" ]; then
            exit 1
        fi
        log "⚠  使用者選擇在 LM Studio 未連接時繼續"
    fi
}

check_image_directory() {
    print_step "檢查圖片目錄..."
    
    if [ ! -d "$IMAGE_DIR" ]; then
        print_warning "圖片目錄不存在：$IMAGE_DIR"
        log "⚠  圖片目錄不存在：$IMAGE_DIR"
        
        # 詢問使用者圖片目錄位置
        echo -e "\n${BOLD}請輸入圖片目錄的完整路徑${NC} (按 Enter 使用預設: ~/Downloads):"
        read -r custom_dir
        
        if [ -z "$custom_dir" ]; then
            IMAGE_DIR="${HOME}/Downloads"
        else
            IMAGE_DIR="$custom_dir"
        fi
        
        if [ ! -d "$IMAGE_DIR" ]; then
            print_error "目錄不存在：$IMAGE_DIR"
            exit 1
        fi
    fi
    
    # 檢查是否有圖片檔案
    image_count=$(find "$IMAGE_DIR" -maxdepth 1 \( -iname "*.jpg" -o -iname "*.jpeg" -o -iname "*.png" -o -iname "*.gif" -o -iname "*.webp" -o -iname "*.bmp" \) -type f 2>/dev/null | wc -l)
    
    if [ "$image_count" -eq 0 ]; then
        print_warning "圖片目錄中沒有找到圖片檔案"
        log "⚠  $IMAGE_DIR 中沒有圖片"
        print_warning "是否繼續？(y/n): "
        read -r response
        if [ "$response" != "y" ]; then
            exit 1
        fi
    else
        print_success "找到 $image_count 個圖片檔案"
        log "✓ 找到 $image_count 個圖片檔案"
    fi
}

check_config_file() {
    print_step "檢查配置文件..."
    
    if [ ! -f "$CONFIG_FILE" ]; then
        print_error "配置文件不存在：$CONFIG_FILE"
        exit 1
    fi
    
    print_success "配置文件已就位"
    log "✓ 配置文件已就位"
}

#######################################################
# 🚀 主執行函數
#######################################################

run_image_analysis() {
    print_step "啟動圖片分析..."
    
    # 激活 Conda 環境
    log "啟動 Conda 環境: $CONDA_ENV"
    
    # 使用 conda run 執行，避免 source 問題
    if conda run -n "$CONDA_ENV" python "${PROJECT_ROOT}/src/full_batch_rename_execute.py" \
        --image_dir "$IMAGE_DIR" \
        --config "$CONFIG_FILE" \
        --log_file "${LOG_DIR}/analysis_${TIMESTAMP}.log" >> "$LOG_FILE" 2>&1; then
        
        print_success "圖片分析完成！"
        log "✓ 圖片分析完成"
        return 0
    else
        print_error "圖片分析失敗"
        log "✗ 圖片分析失敗"
        return 1
    fi
}

show_summary() {
    print_step "生成分析摘要..."
    
    # 查找最新的映射結果
    latest_mapping=$(find "${PROJECT_ROOT}/data" -name "*.json" -type f -printf '%T@ %p\n' 2>/dev/null | sort -rn | head -1 | cut -d' ' -f2-)
    
    if [ -f "$latest_mapping" ]; then
        print_success "分析結果已保存"
        print_info "結果檔案：$latest_mapping"
        log "✓ 結果檔案：$latest_mapping"
        
        # 顯示簡單統計（如果有 jq）
        if command -v jq &> /dev/null; then
            total=$(jq 'length' "$latest_mapping" 2>/dev/null || echo "N/A")
            print_info "已分析檔案數：$total"
            log "已分析檔案數：$total"
        fi
    else
        print_warning "未找到結果檔案"
        log "⚠  未找到結果檔案"
    fi
}

#######################################################
# 📊 主程序流程
#######################################################

main() {
    # 清除終端
    clear
    
    # 顯示歡迎信息
    print_header "🎯 圖片智能命名系統 v1.0"
    
    echo "一鍵執行流程："
    echo "1. ✓ 檢查 Conda 環境"
    echo "2. ✓ 檢查 LM Studio 連接"
    echo "3. ✓ 檢查圖片目錄"
    echo "4. ✓ 啟動分析和命名"
    echo "5. ✓ 生成結果"
    echo ""
    
    # 開始執行前的確認
    print_info "準備開始圖片分析和重新命名"
    echo -e "${BOLD}是否繼續？(y/n): ${NC}"
    read -r response
    
    if [ "$response" != "y" ]; then
        print_warning "操作已取消"
        exit 0
    fi
    
    log "=========================================="
    log "📍 開始執行圖片重新命名流程"
    log "項目目錄：$PROJECT_ROOT"
    log "圖片目錄：$IMAGE_DIR"
    log "=========================================="
    
    # 執行檢查
    check_conda_installed
    check_conda_env_exists
    check_config_file
    check_image_directory
    check_lm_studio
    
    # 執行分析
    echo ""
    print_header "📸 開始圖片分析和重新命名"
    echo -e "${YELLOW}⏱️  這可能需要幾分鐘時間，請耐心等待...${NC}\n"
    
    if run_image_analysis; then
        echo ""
        print_header "✨ 成功完成！"
        show_summary
        
        echo ""
        print_success "圖片重新命名完成！"
        print_info "日誌文件：$LOG_FILE"
        print_info "圖片目錄：$IMAGE_DIR"
        
        log "=========================================="
        log "✓ 圖片重新命名流程完成"
        log "=========================================="
        
        # 詢問是否查看結果
        echo ""
        echo -e "${BOLD}是否打開圖片目錄查看結果？(y/n): ${NC}"
        read -r response
        if [ "$response" = "y" ]; then
            if [ "$(uname)" = "Darwin" ]; then
                open "$IMAGE_DIR"
            elif [ "$(uname)" = "Linux" ]; then
                xdg-open "$IMAGE_DIR" 2>/dev/null || nautilus "$IMAGE_DIR" 2>/dev/null || echo "請手動打開：$IMAGE_DIR"
            fi
        fi
    else
        echo ""
        print_error "圖片分析失敗"
        log "=========================================="
        log "✗ 圖片重新命名流程失敗"
        log "=========================================="
        echo -e "\n${YELLOW}💡 建議：${NC}"
        echo "1. 檢查 LM Studio 是否正在運行"
        echo "2. 檢查網絡連接"
        echo "3. 查看詳細日誌：$LOG_FILE"
        exit 1
    fi
}

# 捕捉 Ctrl+C
trap 'print_error "操作已中止"; log "⚠  使用者中止操作"; exit 130' INT

# 運行主程序
main
