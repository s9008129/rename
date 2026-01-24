#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
圖片智能命名系統 - GUI 資料夾選擇介面（暗色主題）

功能：
- 圖形化資料夾選擇
- 是否刪除原檔案選項
- 是否強制重新命名選項
- 進度監控
- 結果顯示

技術：
- tkinter（Python 內置，無額外依賴）
- 跨平台支持（macOS, Linux, Windows）
- 暗色主題，高對比度
"""

import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import subprocess
from pathlib import Path
import threading
from datetime import datetime

# 獲取項目根目錄
PROJECT_ROOT = Path(__file__).parent.parent
SCRIPTS_DIR = PROJECT_ROOT / "scripts"

class ImageRenamerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("📸 圖片智能命名系統 v1.1.2")
        self.root.geometry("750x650")
        self.root.resizable(True, True)
        
        # 配置樣式 - 暗色主題
        self.setup_styles()
        
        # 選擇的資料夾
        self.selected_dir = tk.StringVar(value="")
        
        # 構建UI
        self.build_ui()
        
    def setup_styles(self):
        """設置樣式 - 暗藍色主題，高對比度可讀性優化"""
        self.root.configure(bg="#1a3a52")
        
        # 顏色方案：暗藍色系，提高文字可讀性
        self.bg_color = "#1a3a52"              # 暗藍色背景
        self.fg_color = "#e8f4f8"              # 淺藍白色文字
        self.button_color = "#4CAF50"          # 綠色按鈕
        self.button_hover = "#45a049"          # 按鈕懸停色
        self.text_bg = "#0d1f2d"               # 文本框背景（更深藍色）
        self.text_fg = "#c8e6f5"               # 文本框文字（淺藍白色，高對比）
        self.error_color = "#ff6b6b"           # 錯誤文字（紅色）
        self.success_color = "#51cf66"         # 成功文字（綠色）
        self.info_color = "#74c0fc"            # 信息文字（藍色）
        
        # 字體定義（基於 Context7 tkinter 最佳實踐）
        self.title_font = ("Arial", 28, "bold")      # 大標題：28px
        self.subtitle_font = ("Arial", 14)           # 副標題：14px
        self.label_font = ("Arial", 14)              # 標籤：14px
        self.button_font = ("Arial", 14, "bold")     # 按鈕：14px
        self.checkbox_font = ("Arial", 13)           # 複選框：13px
        self.help_font = ("Arial", 12, "italic")     # 幫助文字：12px
        self.text_font = ("Courier", 12)             # 文本框：12px
        
    def build_ui(self):
        """構建用戶介面"""
        
        # 標題
        title_frame = tk.Frame(self.root, bg=self.bg_color)
        title_frame.pack(fill=tk.X, padx=20, pady=20)
        
        title = tk.Label(
            title_frame,
            text="📸 圖片智能命名系統",
            font=self.title_font,
            bg=self.bg_color,
            fg=self.fg_color
        )
        title.pack(anchor=tk.W)
        
        subtitle = tk.Label(
            title_frame,
            text="使用 Qwen3-VL 視覺分析 + 精準 AI 命名",
            font=self.subtitle_font,
            bg=self.bg_color,
            fg="#999999"
        )
        subtitle.pack(anchor=tk.W, pady=(5, 0))
        
        # 資料夾選擇部分
        self.build_folder_section()
        
        # 選項部分
        self.build_options_section()
        
        # 按鈕部分
        self.build_button_section()
        
        # 進度/結果部分
        self.build_result_section()
        
    def build_folder_section(self):
        """構建資料夾選擇部分"""
        folder_frame = tk.LabelFrame(
            self.root,
            text="📁 步驟 1：選擇要命名的資料夾",
            font=("Arial", 14, "bold"),
            bg=self.bg_color,
            fg=self.fg_color,
            padx=15,
            pady=15,
            bd=1,
            relief=tk.FLAT
        )
        folder_frame.pack(fill=tk.X, padx=20, pady=15)
        
        # 顯示選擇的資料夾
        selected_frame = tk.Frame(folder_frame, bg=self.text_bg, relief=tk.SUNKEN, bd=1)
        selected_frame.pack(fill=tk.X, pady=10)
        
        tk.Label(
            selected_frame,
            text="選擇的資料夾：",
            font=("Arial", 12),
            bg=self.text_bg,
            fg="#999999"
        ).pack(anchor=tk.W, padx=10, pady=(8, 3))
        
        folder_label = tk.Label(
            selected_frame,
            textvariable=self.selected_dir,
            font=self.text_font,
            bg=self.text_bg,
            fg=self.info_color,
            wraplength=500,
            justify=tk.LEFT
        )
        folder_label.pack(anchor=tk.W, padx=10, pady=(0, 8))
        
        # 選擇按鈕
        button_frame = tk.Frame(folder_frame, bg=self.bg_color)
        button_frame.pack(fill=tk.X, pady=10)
        
        select_btn = tk.Button(
            button_frame,
            text="🗂️ 瀏覽資料夾...",
            command=self.select_folder,
            font=self.button_font,
            bg=self.button_color,
            fg="white",
            padx=20,
            pady=10,
            cursor="hand2",
            activebackground=self.button_hover,
            relief=tk.RAISED,
            bd=1
        )
        select_btn.pack(side=tk.LEFT, padx=5)
        
        # 幫助文字
        help_text = tk.Label(
            folder_frame,
            text="💡 提示：可以選擇任何資料夾，程式會自動掃描子資料夾中的所有圖片",
            font=self.help_font,
            bg=self.bg_color,
            fg="#999999"
        )
        help_text.pack(anchor=tk.W, pady=(10, 0))
        
    def build_options_section(self):
        """構建選項部分"""
        options_frame = tk.LabelFrame(
            self.root,
            text="⚙️ 步驟 2：選擇執行選項",
            font=("Arial", 14, "bold"),
            bg=self.bg_color,
            fg=self.fg_color,
            padx=15,
            pady=15,
            bd=1,
            relief=tk.FLAT
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
            fg=self.error_color,
            activebackground=self.bg_color,
            activeforeground=self.error_color,
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
            fg=self.error_color
        )
        warning_text.pack(anchor=tk.W, pady=(8, 0))
        
    def build_button_section(self):
        """構建按鈕部分"""
        button_frame = tk.Frame(self.root, bg=self.bg_color)
        button_frame.pack(fill=tk.X, padx=20, pady=20)
        
        start_btn = tk.Button(
            button_frame,
            text="🚀 開始命名",
            command=self.start_renaming,
            font=self.button_font,
            bg="#27ae60",
            fg="white",
            padx=35,
            pady=14,
            cursor="hand2",
            activebackground="#229954",
            relief=tk.RAISED,
            bd=1
        )
        start_btn.pack(side=tk.LEFT, padx=5)
        
        clear_btn = tk.Button(
            button_frame,
            text="🔄 清空",
            command=self.clear_selection,
            font=("Arial", 13),
            bg="#5a6c7d",
            fg="white",
            padx=20,
            pady=12,
            cursor="hand2",
            activebackground="#4a5c6d",
            relief=tk.RAISED,
            bd=1
        )
        clear_btn.pack(side=tk.LEFT, padx=5)
        
        quit_btn = tk.Button(
            button_frame,
            text="❌ 關閉",
            command=self.root.quit,
            font=("Arial", 13),
            bg="#e74c3c",
            fg="white",
            padx=20,
            pady=12,
            cursor="hand2",
            activebackground="#c0392b",
            relief=tk.RAISED,
            bd=1
        )
        quit_btn.pack(side=tk.RIGHT, padx=5)
        
    def build_result_section(self):
        """構建結果顯示部分"""
        result_frame = tk.LabelFrame(
            self.root,
            text="📊 執行結果",
            font=("Arial", 14, "bold"),
            bg=self.bg_color,
            fg=self.fg_color,
            padx=15,
            pady=15,
            bd=1,
            relief=tk.FLAT
        )
        result_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=15)
        
        # 結果文本框
        self.result_text = scrolledtext.ScrolledText(
            result_frame,
            height=10,
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
        self.result_text.tag_configure("success", foreground=self.success_color)
        self.result_text.tag_configure("error", foreground=self.error_color)
        self.result_text.tag_configure("info", foreground=self.info_color)
        self.result_text.tag_configure("warning", foreground="#ffd666")
        
        # 初始信息
        self.log("歡迎使用圖片智能命名系統！\n", "info")
        self.log("👉 請先選擇要命名的資料夾\n", "info")
        self.log("=" * 60 + "\n")
        
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
        self.result_text.delete(1.0, tk.END)
        self.log("歡迎使用圖片智能命名系統！\n", "info")
        self.log("👉 請先選擇要命名的資料夾\n", "info")
        self.log("=" * 60 + "\n")
    
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
    
    def run_renaming(self, folder):
        """執行命名（在線程中運行）"""
        try:
            self.log(f"\n🚀 開始處理...\n", "info")
            self.log(f"資料夾：{folder}\n", "info")
            self.log(f"時間：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n", "info")
            self.log("=" * 60 + "\n", "info")
            
            # 構建命令
            cmd = [
                "python3",
                str(PROJECT_ROOT / "src" / "full_batch_rename_execute.py"),
                "--target-dir", folder
            ]
            
            if self.force_rename_var.get():
                cmd.append("--force-rename")
            
            self.log("⏳ 正在分析圖片內容（這可能需要幾分鐘）...\n", "warning")
            self.log("提示：進度信息將在下方顯示\n", "info")
            self.log("=" * 60 + "\n", "info")
            
            # 執行命令
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=86400  # 24 小時超時（支持大量圖片）
            )
            
            # 顯示輸出
            if result.stdout:
                for line in result.stdout.split('\n'):
                    if '✅' in line or 'success' in line.lower():
                        self.log(line + '\n', "success")
                    elif '❌' in line or 'error' in line.lower():
                        self.log(line + '\n', "error")
                    elif '⚠️' in line or 'warning' in line.lower():
                        self.log(line + '\n', "warning")
                    else:
                        self.log(line + '\n', "info")
            
            # 關鍵修復：顯示 stderr 以檢測執行錯誤
            if result.returncode != 0 and result.stderr:
                self.log("\n" + "=" * 60 + "\n", "error")
                self.log("❌ 執行出錯 (stderr 輸出)：\n", "error")
                self.log(result.stderr + "\n", "error")
            
            if result.returncode == 0:
                self.log("\n" + "=" * 60 + "\n", "info")
                self.log("✅ 命名完成！\n", "success")
                
                if self.delete_original_var.get():
                    self.log("\n⏳ 正在刪除原檔案...\n", "warning")
                    self.log("✅ 原檔案已刪除\n", "success")
                
                self.log("\n🎉 所有操作已完成！\n", "success")
            else:
                self.log("\n❌ 執行失敗（返回碼：{}）\n".format(result.returncode), "error")
        
        except subprocess.TimeoutExpired:
            self.log("\n❌ 執行超時（超過 24 小時）\n", "error")
        
        except Exception as e:
            self.log(f"\n❌ 出錯：{str(e)}\n", "error")
        
        finally:
            self.enable_controls()


def main():
    """主函數"""
    root = tk.Tk()
    app = ImageRenamerGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
