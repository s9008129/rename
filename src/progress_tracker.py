#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
進度追蹤系統 - 用於大量圖片批量處理

功能：
- 實時計算進度百分比
- 估計剩餘時間
- 保存進度以支持恢復
- 詳細的分階段日誌

設計原理：
- 最小化記憶體使用（使用文件而不是保存在記憶體）
- 最小化修改影響（不改變核心邏輯）
- 支持長時間運行（可靠的進度追蹤）
"""

import json
from pathlib import Path
from typing import Dict, Optional, List
from datetime import datetime, timedelta
import time


class ProgressTracker:
    """進度追蹤器"""
    
    def __init__(self, session_dir: Path, operation_name: str = "rename"):
        """
        初始化進度追蹤器
        
        Args:
            session_dir: session 目錄（用於保存進度文件）
            operation_name: 操作名稱（用於區分不同操作的進度文件）
        """
        self.session_dir = Path(session_dir)
        self.operation_name = operation_name
        self.session_dir.mkdir(parents=True, exist_ok=True)
        
        # 進度文件
        self.progress_file = self.session_dir / f"progress_{operation_name}.json"
        self.log_file = self.session_dir / f"progress_log_{operation_name}.txt"
        
        # 統計數據
        self.start_time = time.time()
        self.phase = "initializing"
        self.total_files = 0
        self.processed_files = 0
        self.successful_files = 0
        self.failed_files = 0
        
        # 分階段統計
        self.scan_complete = False
        self.analysis_complete = False
        self.rename_complete = False
        
    def _load_progress(self) -> Optional[Dict]:
        """從文件加載進度"""
        if self.progress_file.exists():
            try:
                with open(self.progress_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                return None
        return None
    
    def _save_progress(self):
        """保存進度到文件"""
        progress_data = {
            "timestamp": datetime.now().isoformat(),
            "phase": self.phase,
            "total_files": self.total_files,
            "processed_files": self.processed_files,
            "successful_files": self.successful_files,
            "failed_files": self.failed_files,
            "progress_percent": self.get_progress_percent(),
            "elapsed_time": time.time() - self.start_time,
            "eta_seconds": self.get_eta_seconds(),
            "scan_complete": self.scan_complete,
            "analysis_complete": self.analysis_complete,
            "rename_complete": self.rename_complete,
        }
        
        with open(self.progress_file, 'w', encoding='utf-8') as f:
            json.dump(progress_data, f, ensure_ascii=False, indent=2)
    
    def start_scan(self, total_files: int):
        """開始掃描階段"""
        self.phase = "scanning"
        self.total_files = total_files
        self.processed_files = 0
        self.log(f"📂 開始掃描文件... (總計 {total_files} 個)")
        self._save_progress()
    
    def complete_scan(self):
        """完成掃描階段"""
        self.phase = "scanned"
        self.scan_complete = True
        self.log(f"✅ 掃描完成")
        self._save_progress()
    
    def start_analysis(self):
        """開始分析階段"""
        self.phase = "analyzing"
        self.processed_files = 0
        self.log(f"🤖 開始 LLM 分析 {self.total_files} 張圖片...")
        self._save_progress()
    
    def update_analysis(self, batch_num: int, batch_size: int, processed: int):
        """更新分析進度"""
        self.phase = "analyzing"
        self.processed_files = processed
        progress = self.get_progress_percent()
        eta = self.get_eta_seconds()
        
        eta_str = self._format_time(eta) if eta > 0 else "計算中..."
        
        self.log(
            f"  📦 Batch {batch_num:3d} | 進度 {progress:3d}% | "
            f"已處理 {processed:4d}/{self.total_files} | "
            f"ETA: {eta_str}"
        )
        self._save_progress()
    
    def complete_analysis(self, successful: int, failed: int):
        """完成分析階段"""
        self.phase = "analyzed"
        self.analysis_complete = True
        self.successful_files = successful
        self.failed_files = failed
        self.log(
            f"✅ 分析完成：成功 {successful}/{self.total_files}，失敗 {failed}"
        )
        self._save_progress()
    
    def start_rename(self):
        """開始重命名階段"""
        self.phase = "renaming"
        self.processed_files = 0
        self.log(f"🔄 開始重命名 {self.successful_files} 個文件...")
        self._save_progress()
    
    def update_rename(self, processed: int):
        """更新重命名進度"""
        self.phase = "renaming"
        self.processed_files = processed
        
        # 計算進度（相對於需要重命名的文件數）
        rename_total = self.successful_files
        if rename_total > 0:
            progress = int(processed * 100 / rename_total)
            eta = self.get_eta_seconds()
            eta_str = self._format_time(eta) if eta > 0 else "計算中..."
            
            self.log(
                f"  📝 重命名進度 {progress:3d}% | "
                f"已重命名 {processed:4d}/{rename_total} | "
                f"ETA: {eta_str}"
            )
        self._save_progress()
    
    def complete_rename(self, renamed_count: int, failed_count: int):
        """完成重命名階段"""
        self.phase = "completed"
        self.rename_complete = True
        elapsed = time.time() - self.start_time
        elapsed_str = self._format_time(elapsed)
        
        self.log(
            f"✅ 重命名完成：成功 {renamed_count}，失敗 {failed_count} | "
            f"總耗時：{elapsed_str}"
        )
        self._save_progress()
    
    def get_progress_percent(self) -> int:
        """獲取進度百分比"""
        if self.total_files == 0:
            return 0
        return int(self.processed_files * 100 / self.total_files)
    
    def get_eta_seconds(self) -> float:
        """估計剩餘秒數"""
        if self.processed_files == 0:
            return 0
        
        elapsed = time.time() - self.start_time
        avg_time_per_file = elapsed / self.processed_files
        remaining_files = self.total_files - self.processed_files
        eta = avg_time_per_file * remaining_files
        
        return max(0, eta)
    
    def _format_time(self, seconds: float) -> str:
        """格式化時間"""
        if seconds < 0:
            return "計算中..."
        
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        
        if hours > 0:
            return f"{hours}時 {minutes}分 {secs}秒"
        elif minutes > 0:
            return f"{minutes}分 {secs}秒"
        else:
            return f"{secs}秒"
    
    def log(self, message: str, also_print: bool = True):
        """記錄日誌"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"[{timestamp}] {message}"
        
        # 寫入日誌文件
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(log_message + '\n')
        
        # 同時輸出到終端
        if also_print:
            print(log_message)
    
    def error(self, message: str, also_print: bool = True):
        """記錄錯誤"""
        self.log(f"❌ {message}", also_print)
    
    def warning(self, message: str, also_print: bool = True):
        """記錄警告"""
        self.log(f"⚠️  {message}", also_print)
    
    def get_summary(self) -> Dict:
        """獲取進度摘要"""
        elapsed = time.time() - self.start_time
        return {
            "phase": self.phase,
            "progress_percent": self.get_progress_percent(),
            "processed": self.processed_files,
            "total": self.total_files,
            "successful": self.successful_files,
            "failed": self.failed_files,
            "elapsed_seconds": elapsed,
            "elapsed_formatted": self._format_time(elapsed),
            "eta_seconds": self.get_eta_seconds(),
            "eta_formatted": self._format_time(self.get_eta_seconds()),
        }
