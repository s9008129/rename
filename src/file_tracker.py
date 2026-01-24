#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
智能檔案追蹤和檢測模組
Purpose: 檢測已命名 vs 未命名的檔案，支持增量和強制模式
Author: Development Team
Date: 2026-01-24
"""

import json
import sys
from pathlib import Path
from typing import Set, Dict, List, Tuple
import re

# 全局追蹤檔案位置
PROJECT_ROOT = Path(__file__).parent.parent
TRACKING_DIR = PROJECT_ROOT / "data" / "tracking"
GLOBAL_TRACKER = TRACKING_DIR / ".renamed_tracker.json"


def init_tracking_dir():
    """初始化追蹤目錄"""
    TRACKING_DIR.mkdir(parents=True, exist_ok=True)


def is_already_renamed(filename: str) -> bool:
    """
    檢測檔案是否已被重新命名
    
    方法 1：檢查是否包含中文字符（已命名的特徵）
    方法 2：檢查全局追蹤檔案
    """
    # 方法 1：檢查是否包含中文（最簡單的檢測）
    if contains_chinese(filename):
        return True
    
    # 方法 2：檢查全局追蹤檔案
    if GLOBAL_TRACKER.exists():
        tracker = load_tracker()
        # 檢查任何目錄下的 old_filename
        for dir_path, file_mappings in tracker.get("directories", {}).items():
            if filename in file_mappings.get("files", {}):
                return True
    
    return False


def contains_chinese(text: str) -> bool:
    """檢查字符串是否包含中文字符"""
    # Unicode 範圍：CJK Unified Ideographs
    return bool(re.search(r'[\u4e00-\u9fff]', text))


def load_tracker() -> Dict:
    """加載全局追蹤檔案"""
    init_tracking_dir()
    if GLOBAL_TRACKER.exists():
        with open(GLOBAL_TRACKER, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"directories": {}}


def save_tracker(tracker: Dict):
    """保存全局追蹤檔案"""
    init_tracking_dir()
    with open(GLOBAL_TRACKER, 'w', encoding='utf-8') as f:
        json.dump(tracker, f, ensure_ascii=False, indent=2)


def update_tracker(image_dir: str, old_name: str, new_name: str, status: str = "success"):
    """
    更新全局追蹤檔案
    
    Args:
        image_dir: 圖片目錄路徑
        old_name: 原檔名
        new_name: 新檔名
        status: 狀態（success, failed, skipped）
    """
    tracker = load_tracker()
    
    if image_dir not in tracker["directories"]:
        tracker["directories"][image_dir] = {"files": {}, "summary": {}}
    
    # 記錄映射
    tracker["directories"][image_dir]["files"][old_name] = {
        "new_name": new_name,
        "status": status
    }
    
    save_tracker(tracker)


def analyze_directory(image_dir: str, force_rename: bool = False) -> Tuple[List[str], List[str]]:
    """
    分析目錄中的檔案，返回未命名和已命名的檔案列表
    
    Returns:
        (未命名的檔案列表, 已命名的檔案列表)
    """
    init_tracking_dir()
    
    image_dir_path = Path(image_dir)
    if not image_dir_path.exists():
        raise ValueError(f"目錄不存在：{image_dir}")
    
    # 掃描所有圖片檔案
    image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp'}
    all_images = [
        f.name for f in image_dir_path.iterdir()
        if f.is_file() and f.suffix.lower() in image_extensions
    ]
    
    # 分類
    unnamed_files = []
    renamed_files = []
    
    for filename in all_images:
        if is_already_renamed(filename):
            renamed_files.append(filename)
        else:
            unnamed_files.append(filename)
    
    return unnamed_files, renamed_files


def generate_summary(image_dir: str, unnamed_count: int, renamed_count: int, 
                    force_rename: bool = False) -> str:
    """生成分析摘要"""
    summary = f"""
╔════════════════════════════════════════════════════════╗
║              📊 檔案分析摘要                            ║
╚════════════════════════════════════════════════════════╝

📍 目錄：{image_dir}
📊 統計：
  • 未命名的檔案：{unnamed_count} 個
  • 已命名的檔案：{renamed_count} 個
  • 總計：{unnamed_count + renamed_count} 個

🔧 模式：{'強制重新命名（--force-rename）' if force_rename else '增量模式（默認，跳過已命名）'}

📋 處理計劃：
  {'✓ 重新命名全部檔案（包括已命名的）' if force_rename else '✓ 只命名未命名的檔案'}
  {'✓ 跳過已命名的檔案' if not force_rename else ''}
"""
    return summary


if __name__ == "__main__":
    # 用於測試
    if len(sys.argv) < 2:
        print("使用方式：python3 file_tracker.py <image_dir> [--force-rename]")
        sys.exit(1)
    
    image_dir = sys.argv[1]
    force_rename = "--force-rename" in sys.argv
    
    try:
        unnamed, renamed = analyze_directory(image_dir, force_rename)
        print(generate_summary(image_dir, len(unnamed), len(renamed), force_rename))
        
        if renamed:
            print(f"\n已命名的檔案：")
            for f in renamed[:10]:  # 只顯示前 10 個
                print(f"  • {f}")
            if len(renamed) > 10:
                print(f"  ... 及其他 {len(renamed) - 10} 個")
        
    except Exception as e:
        print(f"❌ 錯誤：{e}", file=sys.stderr)
        sys.exit(1)
