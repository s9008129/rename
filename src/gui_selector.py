#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
圖片智能命名系統 - GUI 資料夾選擇介面（v1.2.2 macOS 設計優化版本）

功能：
- 圖形化資料夾選擇
- 是否刪除原檔案選項
- 是否強制重新命名選項
- 實時進度顯示（進度條、百分比、ETA）
- 結果顯示
- 完成通知

設計特點：
- 符合 macOS Human Interface Guidelines
- 使用原生 ttk.Progressbar
- 藍色、紅色、綠色 macOS 標準色
- 高對比度，文字清晰
- 適當的 padding 和 spacing
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

class ImageRenamerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("📸 圖片智能命名系統 v1.2.2")
        self.root.geometry("800x900")
        self.root.minsize(700, 800)
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
        
        # 字體定義（macOS 規範）
        self.title_font = ("San Francisco", 28, "bold")
        self.subtitle_font = ("San Francisco", 16)
        self.label_font = ("San Francisco", 14)
        self.button_font = ("San Francisco", 14, "bold")
        self.checkbox_font = ("San Francisco", 13)
        self.help_font = ("San Francisco", 12)  # 移除無效的 "regular" 樣式
        self.text_font = ("Menlo", 12)
        self.mono_font = ("Monaco", 11)
        
    def build_ui(self):
        """構建用戶介面"""
        # 主滾動框架（支持響應式布局）
        main_frame = tk.Frame(self.root, bg=self.bg_color)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)
        
        # 標題
        self.build_header(main_frame)
        
        # 資料夾選擇部分
        self.build_folder_section(main_frame)
        
        # 選項部分
        self.build_options_section(main_frame)
        
        # 進度部分
        self.build_progress_section(main_frame)
        
        # 按鈕部分
        self.build_button_section(main_frame)
        
        # 結果部分
        self.build_result_section(main_frame)
        
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


def main():
    """主函數"""
    root = tk.Tk()
    app = ImageRenamerGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
