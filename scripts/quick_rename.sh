#!/bin/bash

#######################################################
# 🎯 一鍵智能命名 - 超簡化版
# 目標：最簡單的操作體驗（按一個鍵，其餘自動化）
#######################################################

set -e

# 顏色
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 路徑
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
IMAGE_DIR="${HOME}/Downloads"
CONDA_ENV="image-rename"

echo ""
echo -e "${BLUE}┌──────────────────────────────────────────────┐${NC}"
echo -e "${BLUE}│${NC} ${BLUE}✨ 圖片智能命名 - 一鍵執行${NC}          ${BLUE}│${NC}"
echo -e "${BLUE}└──────────────────────────────────────────────┘${NC}"
echo ""

# 檢查 Conda
if ! command -v conda &> /dev/null; then
    echo -e "${RED}✗ 找不到 Conda，請先安裝 Miniconda${NC}"
    exit 1
fi

# 檢查/創建環境
echo -e "${YELLOW}🔧 準備環境...${NC}"
if ! conda env list | grep -q "^${CONDA_ENV} "; then
    echo -e "${YELLOW}📦 創建 Conda 環境（約 2-3 分鐘）...${NC}"
    conda env create -f "${PROJECT_ROOT}/environment.yml" -q
fi

# 檢查 LM Studio
echo -e "${YELLOW}🌐 檢查 LM Studio...${NC}"
if ! timeout 2 curl -s http://127.0.0.1:1234/v1/models > /dev/null 2>&1; then
    echo -e "${RED}✗ LM Studio 未運行${NC}"
    echo -e "${YELLOW}💡 請先打開 LM Studio 並加載 qwen3-vl-30b${NC}"
    exit 1
fi

echo -e "${GREEN}✓ 一切就緒${NC}"
echo ""
echo -e "${BLUE}🚀 開始分析圖片...${NC}"
echo -e "${YELLOW}⏱️  可能需要幾分鐘，請耐心等待${NC}\n"

# 執行分析
if conda run -n "$CONDA_ENV" python "${PROJECT_ROOT}/src/full_batch_rename_execute.py" \
    --image_dir "$IMAGE_DIR" \
    --config "${PROJECT_ROOT}/config/config.yaml"; then
    
    echo ""
    echo -e "${GREEN}╔════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║  ✅ 圖片命名完成！                      ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${BLUE}📍 圖片目錄：$IMAGE_DIR${NC}"
    echo ""
    
    # 打開目錄
    if [ "$(uname)" = "Darwin" ]; then
        open "$IMAGE_DIR"
    fi
    
else
    echo -e "${RED}✗ 分析失敗${NC}"
    exit 1
fi
