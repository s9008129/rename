#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
圖片智能命名系統 - GUI 資料夾選擇介面（v1.2.3 完整一頁設計版本）

功能：
- 圖形化資料夾選擇
- 右上角選項控制（強制重新命名、刪除原檔案）
- 實時進度顯示（進度條、百分比、ETA）
- 執行日誌顯示（在選項原本位置）
- 完成通知

設計特點：
- 符合 macOS Human Interface Guidelines
- 單一畫面，無需滾動（全部內容一次看到）
- 右上角浮動選項面板
- 深色背景 + 淺色高對比度文字
- 增大字體，符合蘋果人體工學
- 按鈕文字使用深色（#333 或 #1a1a1a），確保高對比度
"""

import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk
import subprocess
from pathlib import Path
import threading
from datetime import datetime
import re

# 獲取項目根目錄
PROJECT_ROOT = Path(__file__).parent.parent
SCRIPTS_DIR = PROJECT_ROOT / "scripts"

# macOS 標準色（來自 Apple Human Interface Guidelines）
MACOS_BLUE = "#007AFF"        # 主要交互色
MACOS_RED = "#FF3B30"         # 破壞性操作
MACOS_GREEN = "#34C759"       # 成功/確認
MACOS_GRAY = "#8E8E93"        # 次要文字
MACOS_LIGHT_GRAY = "#E5E5EA"  # 分隔線/邊框
DARK_BG = "#1a3a52"           # 暗藍色背景
LIGHT_TEXT = "#e8f4f8"        # 淺藍白色文字
DARK_TEXT_BG = "#0d1f2d"      # 文本框背景
BUTTON_TEXT = "#1a1a1a"       # 按鈕深色文字（高對比度）

class ImageRenamerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("📸 圖片智能命名系統 v1.2.3")
        
        # 根據屏幕尺寸設定視窗大小（符合 macOS 最佳實踐）
        # macOS 上 tkinter 的視窗初始化需要特殊處理
        self.root.withdraw()  # 先隱藏視窗，避免顯示不完整
        self.root.update_idletasks()  # 強制更新以獲取正確的屏幕信息
        
        # 獲取屏幕尺寸
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        # 計算視窗尺寸（屏幕的 75%）
        window_width = int(screen_width * 0.75)
        window_height = int(screen_height * 0.80)
        
        # 確保視窗尺寸合理（最小 1000x700，最大 1400x900）
        window_width = max(1000, min(1400, window_width))
        window_height = max(700, min(900, window_height))
        
        # 計算視窗位置（居中）
        x_pos = (screen_width - window_width) // 2
        y_pos = (screen_height - window_height) // 2
        
        # 設定視窗幾何（位置和大小）
        self.root.geometry(f"{window_width}x{window_height}+{x_pos}+{y_pos}")
        
        # 設定可調整大小，但有最小/最大限制
        self.root.minsize(1000, 700)
        self.root.maxsize(1400, 900)
        self.root.resizable(True, True)
        
        # 配置樣式 - macOS 設計
        self.setup_styles()
        
        # 選擇的資料夾
        self.selected_dir = tk.StringVar(value="")
        
        # 構建UI
        self.build_ui()
        
        # 進度相關變數
        self.current_progress = 0
        self.total_items = 0
        self.is_processing = False
        
        # 保存視窗狀態以備恢復
        self.saved_geometry = None
        
        # 綁定視窗關閉事件，以便保存狀態
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
    def setup_styles(self):
        """設置樣式 - 符合 macOS 設計"""
        self.root.configure(bg=DARK_BG)
        
        # 配置 ttk style（適應 macOS）
        style = ttk.Style()
        style.theme_use('aqua')  # macOS 原生主題
        
        # 顏色方案
        self.bg_color = DARK_BG
        self.fg_color = LIGHT_TEXT
        self.text_bg = DARK_TEXT_BG
        self.text_fg = "#c8e6f5"
        self.error_color = MACOS_RED
        self.success_color = MACOS_GREEN
        self.info_color = MACOS_BLUE
        self.button_primary = MACOS_BLUE
        self.button_danger = MACOS_RED
        self.button_secondary = MACOS_GRAY
        
        # 字體定義（macOS 規範，增大尺寸）
        self.title_font = ("San Francisco", 32, "bold")  # 從 28 增至 32
        self.subtitle_font = ("San Francisco", 20)       # 從 16 增至 20
        self.label_font = ("San Francisco", 16)          # 從 14 增至 16
        self.button_font = ("San Francisco", 15, "bold") # 從 14 增至 15
        self.checkbox_font = ("San Francisco", 15)       # 從 13 增至 15
        self.help_font = ("San Francisco", 14)           # 從 12 增至 14
        self.text_font = ("Menlo", 13)                   # 從 12 增至 13
        self.mono_font = ("Monaco", 12)                  # 從 11 增至 12
        
    def build_ui(self):
        """構建用戶介面 - 響應式單頁佈局"""
        # 主框架（左側主要內容 + 右側選項）
        main_container = tk.Frame(self.root, bg=self.bg_color)
        main_container.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)
        
        # 左側內容區（70% 寬度，自動計算）
        left_frame = tk.Frame(main_container, bg=self.bg_color)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # 右側選項區（30% 寬度，使用 Frame width 屬性）
        right_frame = tk.Frame(main_container, bg=self.bg_color, width=300)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=False, padx=20, pady=20)
        right_frame.pack_propagate(False)  # 防止 Frame 根據內容自動調整大小
        
        # 構建左側內容
        self.build_header(left_frame)
        self.build_folder_section(left_frame)
        self.build_progress_section(left_frame)
        self.build_buttons_section(left_frame)
        
        # 構建右側選項
        self.build_options_section(right_frame)
        
        # 構建結果日誌（在左側最下方，原步驟2位置）
        self.build_result_section(left_frame)
        
        # 顯示視窗（之前隱藏以避免閃爍）
        self.root.deiconify()
        
    def build_header(self, parent):
        """構建標題"""
        header_frame = tk.Frame(parent, bg=self.bg_color)
        header_frame.pack(fill=tk.X, pady=(0, 20))
        
        title = tk.Label(
            header_frame,
            text="📸 圖片智能命名系統",
            font=self.title_font,
            bg=self.bg_color,
            fg=self.fg_color
        )
        title.pack(anchor=tk.W)
        
        subtitle = tk.Label(
            header_frame,
            text="使用 Qwen3-VL 視覺分析 + 精準 AI 命名",
            font=("San Francisco", 14),
            bg=self.bg_color,
            fg=MACOS_GRAY
        )
        subtitle.pack(anchor=tk.W)
        
    def build_folder_section(self, parent):
        """構建資料夾選擇部分"""
        folder_frame = tk.LabelFrame(
            parent,
            text="📁 步驟 1：選擇要命名的資料夾",
            font=("San Francisco", 15, "bold"),
            bg=self.bg_color,
            fg=self.fg_color,
            padx=20,
            pady=15,
            bd=1,
            relief=tk.FLAT,
            labelanchor="nw"
        )
        folder_frame.pack(fill=tk.X, pady=(0, 15))
        
        # 資料夾路徑顯示
        path_label = tk.Label(
            folder_frame,
            text="選擇的資料夾：",
            font=self.label_font,
            bg=self.bg_color,
            fg=self.fg_color
        )
        path_label.pack(anchor=tk.W, pady=(0, 8))
        
        path_display = tk.Entry(
            folder_frame,
            textvariable=self.selected_dir,
            font=self.text_font,
            bg=self.text_bg,
            fg=self.text_fg,
            insertbackground=self.text_fg,
            bd=1,
            relief=tk.SOLID,
            state="readonly"
        )
        path_display.pack(fill=tk.X, pady=(0, 12))
        
        # 選擇按鈕
        select_btn = tk.Button(
            folder_frame,
            text="🗂️ 瀏覽資料夾...",
            command=self.select_folder,
            font=self.button_font,
            bg=MACOS_BLUE,
            fg=BUTTON_TEXT,  # 深色文字而非白色
            padx=20,
            pady=10,
            cursor="hand2",
            activebackground="#0051CC",
            activeforeground=BUTTON_TEXT,  # 深色文字
            relief=tk.RAISED,
            bd=0,
            highlightthickness=0
        )
        select_btn.pack(side=tk.LEFT, padx=0)
        
        # 幫助文字
        help_text = tk.Label(
            folder_frame,
            text="💡 提示：可以選擇任何資料夾，程式會自動掃描子資料夾中的所有圖片",
            font=self.help_font,
            bg=self.bg_color,
            fg=MACOS_GRAY
        )
        help_text.pack(anchor=tk.W, pady=(12, 0))
        
    def build_progress_section(self, parent):
        """構建進度部分"""
        progress_frame = tk.LabelFrame(
            parent,
            text="📊 執行進度",
            font=("San Francisco", 15, "bold"),
            bg=self.bg_color,
            fg=self.fg_color,
            padx=20,
            pady=15,
            bd=1,
            relief=tk.FLAT,
            labelanchor="nw"
        )
        progress_frame.pack(fill=tk.X, pady=(0, 15))
        
        # 進度百分比
        self.progress_label = tk.Label(
            progress_frame,
            text="進度：等待開始",
            font=self.label_font,
            bg=self.bg_color,
            fg=self.info_color
        )
        self.progress_label.pack(anchor=tk.W, pady=(0, 10))
        
        # 進度條（使用 ttk，macOS 原生樣式）
        self.progress_bar = ttk.Progressbar(
            progress_frame,
            length=500,
            mode='determinate',
            value=0,
            maximum=100
        )
        self.progress_bar.pack(fill=tk.X, pady=10)
        
        # ETA 標籤
        self.eta_label = tk.Label(
            progress_frame,
            text="ETA：計算中...",
            font=self.help_font,
            bg=self.bg_color,
            fg=MACOS_GRAY
        )
        self.eta_label.pack(anchor=tk.W, pady=(10, 0))
        
        # 當前步驟
        self.step_label = tk.Label(
            progress_frame,
            text="",
            font=self.help_font,
            bg=self.bg_color,
            fg=MACOS_GRAY
        )
        self.step_label.pack(anchor=tk.W, pady=(5, 0))
        
    def build_buttons_section(self, parent):
        """構建按鈕部分"""
        button_frame = tk.Frame(parent, bg=self.bg_color)
        button_frame.pack(fill=tk.X, pady=(0, 15))
        
        # 開始按鈕（藍色，主要操作）
        start_btn = tk.Button(
            button_frame,
            text="🚀 開始命名",
            command=self.start_renaming,
            font=self.button_font,
            bg=MACOS_BLUE,
            fg=BUTTON_TEXT,  # 深色文字而非白色
            padx=24,
            pady=10,
            cursor="hand2",
            activebackground="#0051CC",
            activeforeground=BUTTON_TEXT,  # 深色文字
            relief=tk.RAISED,
            bd=0,
            highlightthickness=0
        )
        start_btn.pack(side=tk.LEFT, padx=5)
        
        # 清空按鈕（灰色，次要操作）
        clear_btn = tk.Button(
            button_frame,
            text="🔄 清空",
            command=self.clear_selection,
            font=self.button_font,
            bg=MACOS_GRAY,
            fg=BUTTON_TEXT,  # 深色文字而非白色
            padx=20,
            pady=10,
            cursor="hand2",
            activebackground="#72747D",
            activeforeground=BUTTON_TEXT,  # 深色文字
            relief=tk.RAISED,
            bd=0,
            highlightthickness=0
        )
        clear_btn.pack(side=tk.LEFT, padx=5)
        
        # 關閉按鈕（紅色，破壞性操作）
        quit_btn = tk.Button(
            button_frame,
            text="❌ 關閉",
            command=self.root.quit,
            font=self.button_font,
            bg=MACOS_RED,
            fg="white",  # 白色文字在紅色背景上清晰
            padx=20,
            pady=10,
            cursor="hand2",
            activebackground="#CC1410",
            activeforeground="white",
            relief=tk.RAISED,
            bd=0,
            highlightthickness=0
        )
        quit_btn.pack(side=tk.RIGHT, padx=5)
        
    def build_options_section(self, parent):
        """構建右上角選項部分"""
        options_frame = tk.LabelFrame(
            parent,
            text="⚙️ 執行選項",
            font=("San Francisco", 14, "bold"),
            bg=self.bg_color,
            fg=self.fg_color,
            padx=15,
            pady=15,
            bd=1,
            relief=tk.FLAT,
            labelanchor="nw"
        )
        options_frame.pack(fill=tk.X, pady=(0, 20))
        
        # 強制重新命名
        self.force_rename_var = tk.BooleanVar(value=False)
        force_checkbox = tk.Checkbutton(
            options_frame,
            text="🔄 強制重新命名",
            variable=self.force_rename_var,
            font=self.checkbox_font,
            bg=self.bg_color,
            fg=self.fg_color,
            activebackground=self.bg_color,
            activeforeground=self.fg_color,
            selectcolor=self.text_bg,
            cursor="hand2"
        )
        force_checkbox.pack(anchor=tk.W, pady=8)
        
        force_help = tk.Label(
            options_frame,
            text="重新分析所有檔案\n包括已命名的",
            font=("San Francisco", 12),
            bg=self.bg_color,
            fg=MACOS_GRAY,
            justify=tk.LEFT
        )
        force_help.pack(anchor=tk.W, padx=(20, 0), pady=(0, 8))
        
        # 刪除原檔案
        self.delete_original_var = tk.BooleanVar(value=False)
        delete_checkbox = tk.Checkbutton(
            options_frame,
            text="🗑️ 刪除原檔案",
            variable=self.delete_original_var,
            font=self.checkbox_font,
            bg=self.bg_color,
            fg=MACOS_RED,
            activebackground=self.bg_color,
            activeforeground=MACOS_RED,
            selectcolor=self.text_bg,
            cursor="hand2"
        )
        delete_checkbox.pack(anchor=tk.W, pady=8)
        
        delete_help = tk.Label(
            options_frame,
            text="保留新檔名\n刪除舊檔名",
            font=("San Francisco", 12),
            bg=self.bg_color,
            fg=MACOS_RED,
            justify=tk.LEFT
        )
        delete_help.pack(anchor=tk.W, padx=(20, 0), pady=(0, 8))
        
        # 警告文字
        warning_text = tk.Label(
            options_frame,
            text="⚠️ 警告：無法復原！",
            font=self.help_font,
            bg=self.bg_color,
            fg=MACOS_RED
        )
        warning_text.pack(anchor=tk.W, pady=(8, 0))
        
    def build_result_section(self, parent):
        """構建結果顯示部分（在原步驟2位置）"""
        result_frame = tk.LabelFrame(
            parent,
            text="📋 執行日誌",
            font=("San Francisco", 15, "bold"),
            bg=self.bg_color,
            fg=self.fg_color,
            padx=15,
            pady=15,
            bd=1,
            relief=tk.FLAT,
            labelanchor="nw"
        )
        result_frame.pack(fill=tk.BOTH, expand=True, pady=(15, 0))
        
        # 結果顯示框
        self.result_text = scrolledtext.ScrolledText(
            result_frame,
            font=self.text_font,
            bg=self.text_bg,
            fg=self.text_fg,
            insertbackground=self.text_fg,
            height=6,  # 最小高度
            width=50,
            bd=1,
            relief=tk.SOLID,
            wrap=tk.WORD
        )
        self.result_text.pack(fill=tk.BOTH, expand=True)
        
        # 配置結果文本的色彩標籤
        self.result_text.tag_configure("success", foreground=MACOS_GREEN)
        self.result_text.tag_configure("error", foreground=MACOS_RED)
        self.result_text.tag_configure("info", foreground=MACOS_BLUE)
        self.result_text.tag_configure("warning", foreground="#FF9500")
        
    def select_folder(self):
        """選擇資料夾"""
        folder = filedialog.askdirectory(
            title="選擇要命名的圖片資料夾",
            initialdir=str(Path.home() / "Downloads")
        )
        if folder:
            self.selected_dir.set(folder)
            self.log(f"✅ 選擇了資料夾：{folder}\n", "info")
            
    def clear_selection(self):
        """清空選擇"""
        self.selected_dir.set("")
        self.result_text.delete(1.0, tk.END)
        
    def start_renaming(self):
        """開始重命名"""
        if not self.selected_dir.get():
            messagebox.showwarning("提示", "請先選擇一個資料夾")
            return
            
        if self.is_processing:
            messagebox.showwarning("提示", "正在處理中，請稍候...")
            return
        
        self.is_processing = True
        self.result_text.delete(1.0, tk.END)
        self.log("🚀 開始執行重命名...\n", "info")
        
        # 在另一個線程中運行重命名
        thread = threading.Thread(target=self.run_renaming)
        thread.daemon = True
        thread.start()
        
    def run_renaming(self):
        """執行重命名（在后台線程）"""
        try:
            target_dir = self.selected_dir.get()
            cmd = [
                "python3",
                str(PROJECT_ROOT / "src" / "full_batch_rename_execute.py"),
                "--target", target_dir
            ]
            
            if self.force_rename_var.get():
                cmd.append("--force-rename")
            
            if self.delete_original_var.get():
                cmd.append("--delete-original")
            
            # 執行 subprocess，實時捕獲輸出
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1
            )
            
            # 讀取 stdout
            for line in process.stdout:
                self.parse_and_display(line)
            
            # 讀取 stderr
            for line in process.stderr:
                self.log(line, "error")
            
            process.wait()
            
            if process.returncode == 0:
                self.log("\n✅ 重命名完成！\n", "success")
                messagebox.showinfo("完成", "圖片重命名已完成！")
            else:
                self.log(f"\n❌ 重命名失敗（錯誤碼：{process.returncode}）\n", "error")
                
        except Exception as e:
            self.log(f"❌ 執行出錯：{str(e)}\n", "error")
        finally:
            self.is_processing = False
            
    def parse_and_display(self, line):
        """解析並顯示輸出"""
        line = line.rstrip('\n')
        
        if "[進度]" in line:
            # 解析進度訊息
            match = re.search(r'\[進度\]\s+(\S+):\s+(\d+)%\s+\|\s+(\d+)/(\d+)\s+\|\s+ETA:\s+(.+)', line)
            if match:
                step = match.group(1)
                pct = int(match.group(2))
                current = int(match.group(3))
                total = int(match.group(4))
                eta = match.group(5)
                
                self.progress_label.config(text=f"進度：{pct}% ({current}/{total})")
                self.progress_bar["value"] = pct
                self.eta_label.config(text=f"ETA：{eta}")
                self.step_label.config(text=f"正在執行：{step}")
                self.log(line + "\n", "info")
        elif "[完成]" in line:
            self.progress_bar["value"] = 100
            self.progress_label.config(text="進度：100% (完成！)")
            self.log(line + "\n", "success")
        elif line.startswith("✅"):
            self.log(line + "\n", "success")
        elif line.startswith("❌"):
            self.log(line + "\n", "error")
        elif line.startswith("⚠️"):
            self.log(line + "\n", "warning")
        else:
            self.log(line + "\n", "info")
            
    def log(self, message, tag="info"):
        """記錄消息"""
        self.result_text.insert(tk.END, message, tag)
        self.result_text.see(tk.END)
        self.root.update()


def main():
    root = tk.Tk()
    app = ImageRenamerGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()

        
        
    def setup_styles(self):
        """設置樣式 - 符合 macOS 設計"""
        self.root.configure(bg=DARK_BG)
        
        # 配置 ttk style（適應 macOS）
        style = ttk.Style()
        style.theme_use('aqua')  # macOS 原生主題
        
        # 顏色方案
        self.bg_color = DARK_BG
        self.fg_color = LIGHT_TEXT
        self.text_bg = DARK_TEXT_BG
        self.text_fg = "#c8e6f5"
        self.error_color = MACOS_RED
        self.success_color = MACOS_GREEN
        self.info_color = MACOS_BLUE
        self.button_primary = MACOS_BLUE
        self.button_danger = MACOS_RED
        self.button_secondary = MACOS_GRAY
        
        # 字體定義（macOS 規範，增大尺寸）
        self.title_font = ("San Francisco", 32, "bold")  # 從 28 增至 32
        self.subtitle_font = ("San Francisco", 20)       # 從 16 增至 20
        self.label_font = ("San Francisco", 16)          # 從 14 增至 16
        self.button_font = ("San Francisco", 15, "bold") # 從 14 增至 15
        self.checkbox_font = ("San Francisco", 15)       # 從 13 增至 15
        self.help_font = ("San Francisco", 14)           # 從 12 增至 14
        self.text_font = ("Menlo", 13)                   # 從 12 增至 13
        self.mono_font = ("Monaco", 12)                  # 從 11 增至 12
        
    # 其他舊方法已全部替換為新的單頁設計
    
    
def main():
    root = tk.Tk()
    app = ImageRenamerGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
        
    def build_header(self, parent):
        """構建標題"""
        header_frame = tk.Frame(parent, bg=self.bg_color)
        header_frame.pack(fill=tk.X, padx=24, pady=(20, 10))
        
        title = tk.Label(
            header_frame,
            text="📸 圖片智能命名系統",
            font=self.title_font,
            bg=self.bg_color,
            fg=self.fg_color
        )
        title.pack(anchor=tk.W)
        
        subtitle = tk.Label(
            header_frame,
            text="使用 Qwen3-VL 視覺分析 + 精準 AI 命名",
            font=self.subtitle_font,
            bg=self.bg_color,
            fg=MACOS_GRAY
        )
        subtitle.pack(anchor=tk.W, pady=(5, 0))
        
    def build_folder_section(self, parent):
        """構建資料夾選擇部分"""
        folder_frame = tk.LabelFrame(
            parent,
            text="📁 步驟 1：選擇要命名的資料夾",
            font=("San Francisco", 13, "bold"),
            bg=self.bg_color,
            fg=self.fg_color,
            padx=20,
            pady=15,
            bd=1,
            relief=tk.FLAT,
            labelanchor="nw"
        )
        folder_frame.pack(fill=tk.X, padx=20, pady=15)
        
        # 顯示選擇的資料夾
        selected_frame = tk.Frame(folder_frame, bg=self.text_bg, relief=tk.SUNKEN, bd=1)
        selected_frame.pack(fill=tk.X, pady=10)
        
        tk.Label(
            selected_frame,
            text="選擇的資料夾：",
            font=("San Francisco", 11),
            bg=self.text_bg,
            fg=MACOS_GRAY
        ).pack(anchor=tk.W, padx=12, pady=(8, 3))
        
        folder_label = tk.Label(
            selected_frame,
            textvariable=self.selected_dir,
            font=self.mono_font,
            bg=self.text_bg,
            fg=self.info_color,
            wraplength=700,
            justify=tk.LEFT
        )
        folder_label.pack(anchor=tk.W, padx=12, pady=(0, 8))
        
        # 選擇按鈕（藍色，macOS 標準）
        button_frame = tk.Frame(folder_frame, bg=self.bg_color)
        button_frame.pack(fill=tk.X, pady=10)
        
        select_btn = tk.Button(
            button_frame,
            text="🗂️ 瀏覽資料夾...",
            command=self.select_folder,
            font=self.button_font,
            bg=self.button_primary,
            fg="white",
            padx=24,
            pady=10,
            cursor="hand2",
            activebackground="#0051CC",
            relief=tk.RAISED,
            bd=0,
            highlightthickness=0
        )
        select_btn.pack(side=tk.LEFT, padx=5)
        
        # 幫助文字
        help_text = tk.Label(
            folder_frame,
            text="💡 提示：可以選擇任何資料夾，程式會自動掃描子資料夾中的所有圖片",
            font=self.help_font,
            bg=self.bg_color,
            fg=MACOS_GRAY
        )
        help_text.pack(anchor=tk.W, pady=(10, 0))
        
    def build_options_section(self, parent):
        """構建選項部分"""
        options_frame = tk.LabelFrame(
            parent,
            text="⚙️ 步驟 2：選擇執行選項",
            font=("San Francisco", 13, "bold"),
            bg=self.bg_color,
            fg=self.fg_color,
            padx=20,
            pady=15,
            bd=1,
            relief=tk.FLAT,
            labelanchor="nw"
        )
        options_frame.pack(fill=tk.X, padx=20, pady=15)
        
        # 強制重新命名
        self.force_rename_var = tk.BooleanVar(value=False)
        force_checkbox = tk.Checkbutton(
            options_frame,
            text="🔄 強制重新命名（重新分析所有檔案，包括已命名的）",
            variable=self.force_rename_var,
            font=self.checkbox_font,
            bg=self.bg_color,
            fg=self.fg_color,
            activebackground=self.bg_color,
            activeforeground=self.fg_color,
            selectcolor=self.text_bg,
            cursor="hand2"
        )
        force_checkbox.pack(anchor=tk.W, pady=8)
        
        # 刪除原檔案
        self.delete_original_var = tk.BooleanVar(value=False)
        delete_checkbox = tk.Checkbutton(
            options_frame,
            text="🗑️ 刪除原檔案（保留重命名後的檔案，刪除命名前的檔案）",
            variable=self.delete_original_var,
            font=self.checkbox_font,
            bg=self.bg_color,
            fg=MACOS_RED,
            activebackground=self.bg_color,
            activeforeground=MACOS_RED,
            selectcolor=self.text_bg,
            cursor="hand2"
        )
        delete_checkbox.pack(anchor=tk.W, pady=8)
        
        # 警告文字
        warning_text = tk.Label(
            options_frame,
            text="⚠️ 注意：刪除原檔案操作無法復原！",
            font=self.help_font,
            bg=self.bg_color,
            fg=MACOS_RED
        )
        warning_text.pack(anchor=tk.W, pady=(8, 0))
        
    def build_progress_section(self, parent):
        """構建進度部分"""
        progress_frame = tk.LabelFrame(
            parent,
            text="📊 執行進度",
            font=("San Francisco", 13, "bold"),
            bg=self.bg_color,
            fg=self.fg_color,
            padx=20,
            pady=15,
            bd=1,
            relief=tk.FLAT,
            labelanchor="nw"
        )
        progress_frame.pack(fill=tk.X, padx=20, pady=15)
        
        # 進度百分比
        self.progress_label = tk.Label(
            progress_frame,
            text="進度：等待開始",
            font=("San Francisco", 12),
            bg=self.bg_color,
            fg=self.info_color
        )
        self.progress_label.pack(anchor=tk.W, pady=(0, 10))
        
        # 進度條（使用 ttk，macOS 原生樣式）
        self.progress_bar = ttk.Progressbar(
            progress_frame,
            length=600,
            mode='determinate',
            value=0,
            maximum=100
        )
        self.progress_bar.pack(fill=tk.X, pady=10)
        
        # ETA 標籤
        self.eta_label = tk.Label(
            progress_frame,
            text="ETA：計算中...",
            font=("San Francisco", 11),
            bg=self.bg_color,
            fg=MACOS_GRAY
        )
        self.eta_label.pack(anchor=tk.W, pady=(10, 0))
        
        # 當前步驟
        self.step_label = tk.Label(
            progress_frame,
            text="",
            font=("San Francisco", 11),
            bg=self.bg_color,
            fg=MACOS_GRAY
        )
        self.step_label.pack(anchor=tk.W, pady=(5, 0))
        
    def build_button_section(self, parent):
        """構建按鈕部分"""
        button_frame = tk.Frame(parent, bg=self.bg_color)
        button_frame.pack(fill=tk.X, padx=20, pady=20)
        
        # 開始按鈕（藍色，主要操作）
        start_btn = tk.Button(
            button_frame,
            text="🚀 開始命名",
            command=self.start_renaming,
            font=self.button_font,
            bg=MACOS_BLUE,
            fg="white",
            padx=32,
            pady=12,
            cursor="hand2",
            activebackground="#0051CC",
            relief=tk.RAISED,
            bd=0,
            highlightthickness=0
        )
        start_btn.pack(side=tk.LEFT, padx=5)
        
        # 清空按鈕（灰色，次要操作）
        clear_btn = tk.Button(
            button_frame,
            text="🔄 清空",
            command=self.clear_selection,
            font=("San Francisco", 13),
            bg=MACOS_GRAY,
            fg="white",
            padx=20,
            pady=10,
            cursor="hand2",
            activebackground="#72747D",
            relief=tk.RAISED,
            bd=0,
            highlightthickness=0
        )
        clear_btn.pack(side=tk.LEFT, padx=5)
        
        # 關閉按鈕（紅色，破壞性操作）
        quit_btn = tk.Button(
            button_frame,
            text="❌ 關閉",
            command=self.root.quit,
            font=("San Francisco", 13),
            bg=MACOS_RED,
            fg="white",
            padx=20,
            pady=10,
            cursor="hand2",
            activebackground="#CC1410",
            relief=tk.RAISED,
            bd=0,
            highlightthickness=0
        )
        quit_btn.pack(side=tk.RIGHT, padx=5)
        
    def build_result_section(self, parent):
        """構建結果顯示部分"""
        result_frame = tk.LabelFrame(
            parent,
            text="📋 執行日誌",
            font=("San Francisco", 13, "bold"),
            bg=self.bg_color,
            fg=self.fg_color,
            padx=15,
            pady=15,
            bd=1,
            relief=tk.FLAT,
            labelanchor="nw"
        )
        result_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=15)
        
        # 結果文本框
        self.result_text = scrolledtext.ScrolledText(
            result_frame,
            height=12,
            font=self.text_font,
            bg=self.text_bg,
            fg=self.text_fg,
            wrap=tk.WORD,
            insertbackground=self.text_fg,
            relief=tk.SUNKEN,
            bd=1
        )
        self.result_text.pack(fill=tk.BOTH, expand=True)
        
        # 配置顏色標籤
        self.result_text.tag_configure("success", foreground=MACOS_GREEN)
        self.result_text.tag_configure("error", foreground=MACOS_RED)
        self.result_text.tag_configure("info", foreground=MACOS_BLUE)
        self.result_text.tag_configure("warning", foreground="#FFD60A")
        self.result_text.tag_configure("completed", foreground=MACOS_GREEN, background=self.text_bg)
        
        # 初始信息
        self.log("歡迎使用圖片智能命名系統！\n", "info")
        self.log("👉 請先選擇要命名的資料夾\n", "info")
        
    def log(self, message, tag="info"):
        """在結果框中記錄信息"""
        self.result_text.insert(tk.END, message, tag)
        self.result_text.see(tk.END)
        self.root.update()
        
    def select_folder(self):
        """選擇資料夾"""
        folder = filedialog.askdirectory(
            title="選擇要命名的圖片資料夾",
            initialdir=str(Path.home())
        )
        
        if folder:
            self.selected_dir.set(folder)
            self.log(f"\n✅ 已選擇資料夾：{folder}\n", "success")
            
            # 掃描並顯示統計信息
            self.show_folder_info(folder)
    
    def show_folder_info(self, folder_path):
        """顯示資料夾信息"""
        try:
            path = Path(folder_path)
            
            # 統計圖片
            image_extensions = {'.png', '.jpg', '.jpeg', '.webp', '.gif', '.bmp'}
            image_files = [
                f for f in path.rglob("*")
                if f.is_file() and f.suffix.lower() in image_extensions
            ]
            
            # 統計子資料夾
            subdirs = [d for d in path.rglob("*") if d.is_dir()]
            
            info = f"""
📈 資料夾統計信息：
  • 總圖片數：{len(image_files)} 個
  • 子資料夾：{len(subdirs)} 個
  • 掃描範圍：所有嵌套目錄（包括子資料夾）
"""
            self.log(info, "info")
            
        except Exception as e:
            self.log(f"\n⚠️ 掃描資料夾時出錯：{str(e)}\n", "error")
    
    def clear_selection(self):
        """清空選擇"""
        self.selected_dir.set("")
        self.force_rename_var.set(False)
        self.delete_original_var.set(False)
        self.progress_bar['value'] = 0
        self.progress_label.config(text="進度：等待開始")
        self.eta_label.config(text="ETA：計算中...")
        self.step_label.config(text="")
        self.result_text.delete(1.0, tk.END)
        self.log("歡迎使用圖片智能命名系統！\n", "info")
        self.log("👉 請先選擇要命名的資料夾\n", "info")
    
    def start_renaming(self):
        """開始命名"""
        folder = self.selected_dir.get()
        
        if not folder or not Path(folder).exists():
            messagebox.showerror(
                "錯誤",
                "❌ 請先選擇一個有效的資料夾"
            )
            return
        
        if self.delete_original_var.get():
            response = messagebox.askyesnocancel(
                "確認刪除原檔案",
                "⚠️ 您選擇了刪除原檔案。\n\n此操作無法復原！\n\n是否繼續？"
            )
            if response is None or response is False:
                return
        
        # 禁用按鈕
        self.disable_controls()
        self.is_processing = True
        
        # 在新線程中執行命名
        thread = threading.Thread(
            target=self.run_renaming,
            args=(folder,)
        )
        thread.daemon = True
        thread.start()
    
    def disable_controls(self):
        """禁用控制項"""
        for widget in self.root.winfo_children():
            self._disable_widget_recursively(widget)
    
    def _disable_widget_recursively(self, widget):
        """遞迴禁用控件"""
        if isinstance(widget, (tk.Button, tk.Checkbutton)):
            widget.config(state=tk.DISABLED)
        for child in widget.winfo_children():
            self._disable_widget_recursively(child)
    
    def enable_controls(self):
        """啟用控制項"""
        for widget in self.root.winfo_children():
            self._enable_widget_recursively(widget)
    
    def _enable_widget_recursively(self, widget):
        """遞迴啟用控件"""
        if isinstance(widget, (tk.Button, tk.Checkbutton)):
            widget.config(state=tk.NORMAL)
        for child in widget.winfo_children():
            self._enable_widget_recursively(child)
    
    def parse_progress(self, line):
        """解析進度訊息"""
        # 匹配 [進度] 格式的訊息
        match = re.search(r'\[進度\]\s+(\S+):\s+(\d+)%\s+\|\s+(\d+)/(\d+)\s+\|\s+ETA:\s+(.+)', line)
        if match:
            step = match.group(1)  # 分析/重命名
            progress = int(match.group(2))
            current = int(match.group(3))
            total = int(match.group(4))
            eta = match.group(5)
            
            return {
                'step': step,
                'progress': progress,
                'current': current,
                'total': total,
                'eta': eta
            }
        return None
    
    def update_progress_ui(self, progress_data):
        """更新進度 UI"""
        if progress_data:
            progress = progress_data['progress']
            step = progress_data['step']
            current = progress_data['current']
            total = progress_data['total']
            eta = progress_data['eta']
            
            self.progress_bar['value'] = progress
            self.progress_label.config(text=f"進度：{progress}% ({current}/{total})")
            self.eta_label.config(text=f"ETA：{eta}")
            self.step_label.config(text=f"正在執行：{step}")
            self.root.update()
    
    def run_renaming(self, folder):
        """執行命名（在線程中運行）"""
        try:
            self.log(f"\n🚀 開始處理...\n", "info")
            self.log(f"資料夾：{folder}\n", "info")
            self.log(f"時間：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n", "info")
            self.log("=" * 70 + "\n", "info")
            
            # 構建命令
            cmd = [
                "python3",
                str(PROJECT_ROOT / "src" / "full_batch_rename_execute.py"),
                "--target-dir", folder
            ]
            
            if self.force_rename_var.get():
                cmd.append("--force-rename")
            
            if self.delete_original_var.get():
                cmd.append("--delete-original")
            
            self.log("⏳ 正在分析圖片內容（這可能需要幾分鐘）...\n", "warning")
            self.log("提示：進度信息將在下方實時顯示\n", "info")
            self.log("=" * 70 + "\n", "info")
            
            # 使用 Popen 實現實時輸出捕獲
            import select
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1  # 行緩衝，確保實時輸出
            )
            
            # 同時監視 stdout 和 stderr
            try:
                while True:
                    # 使用 select 同時讀取 stdout 和 stderr
                    ready_fds, _, _ = select.select(
                        [process.stdout, process.stderr],
                        [], [],
                        0.1  # 100ms 超時
                    )
                    
                    for fd in ready_fds:
                        line = fd.readline()
                        if line:
                            line = line.rstrip('\n')
                            if line:
                                # 嘗試解析進度訊息
                                progress_data = self.parse_progress(line)
                                if progress_data:
                                    self.update_progress_ui(progress_data)
                                
                                # 根據內容選擇顏色標籤
                                if fd == process.stderr:
                                    self.log(line + '\n', "error")
                                elif '[完成]' in line:
                                    self.log(line + '\n', "success")
                                elif '✅' in line or 'success' in line.lower():
                                    self.log(line + '\n', "success")
                                elif '❌' in line or 'error' in line.lower():
                                    self.log(line + '\n', "error")
                                elif '⚠️' in line or '⏳' in line or 'warning' in line.lower():
                                    self.log(line + '\n', "warning")
                                else:
                                    self.log(line + '\n', "info")
                    
                    # 檢查進程是否完成
                    if process.poll() is not None:
                        break
                
                # 讀取任何剩餘的輸出
                remaining_stdout = process.stdout.read()
                if remaining_stdout:
                    for line in remaining_stdout.split('\n'):
                        if line:
                            self.log(line + '\n', "info")
                
                remaining_stderr = process.stderr.read()
                if remaining_stderr:
                    for line in remaining_stderr.split('\n'):
                        if line:
                            self.log(line + '\n', "error")
                
            except Exception as e:
                self.log(f"\n⚠️ 讀取輸出出錯：{str(e)}\n", "warning")
            
            # 檢查返回碼
            return_code = process.returncode
            
            if return_code == 0:
                self.log("\n" + "=" * 70 + "\n", "success")
                self.log("✅ 命名完成！\n", "success")
                self.log("\n🎉 所有操作已完成！\n", "success")
                
                # 設置進度條為 100%
                self.progress_bar['value'] = 100
                self.progress_label.config(text="進度：100% (完成)")
                self.step_label.config(text="狀態：✅ 所有操作已完成")
                
                # 成功提示
                messagebox.showinfo(
                    "操作完成",
                    "✅ 圖片命名已完成！\n\n所有圖片已成功重命名。"
                )
            else:
                self.log("\n❌ 執行失敗（返回碼：{}）\n".format(return_code), "error")
                
                # 失敗提示
                messagebox.showerror(
                    "操作失敗",
                    f"❌ 執行失敗，返回碼：{return_code}"
                )
        
        except Exception as e:
            self.log(f"\n❌ 出錯：{str(e)}\n", "error")
            import traceback
            self.log(f"詳細信息：{traceback.format_exc()}\n", "error")
        
        finally:
            self.is_processing = False
            self.enable_controls()

    def on_closing(self):
        """處理視窗關閉事件"""
        self.root.destroy()


def main():
    """主函數"""
    root = tk.Tk()
    app = ImageRenamerGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
