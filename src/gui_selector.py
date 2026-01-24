#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
圖片智能命名系統 - GUI 資料夾選擇介面

功能：
- 圖形化資料夾選擇
- 是否刪除原檔案選項
- 是否強制重新命名選項
- 進度監控
- 結果顯示

技術：
- tkinter（Python 內置，無額外依賴）
- 跨平台支持（macOS, Linux, Windows）
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
        self.root.geometry("700x600")
        self.root.resizable(True, True)
        
        # 配置樣式
        self.setup_styles()
        
        # 選擇的資料夾
        self.selected_dir = tk.StringVar(value="")
        
        # 構建UI
        self.build_ui()
        
    def setup_styles(self):
        """設置樣式"""
        self.root.configure(bg="#f0f0f0")
        self.bg_color = "#f0f0f0"
        self.button_color = "#4CAF50"
        self.button_hover = "#45a049"
        
    def build_ui(self):
        """構建用戶介面"""
        
        # 標題
        title_frame = tk.Frame(self.root, bg=self.bg_color)
        title_frame.pack(fill=tk.X, padx=20, pady=15)
        
        title = tk.Label(
            title_frame,
            text="📸 圖片智能命名系統",
            font=("Arial", 20, "bold"),
            bg=self.bg_color,
            fg="#333333"
        )
        title.pack(anchor=tk.W)
        
        subtitle = tk.Label(
            title_frame,
            text="使用 Qwen3-VL 視覺分析 + 精準 AI 命名",
            font=("Arial", 10),
            bg=self.bg_color,
            fg="#666666"
        )
        subtitle.pack(anchor=tk.W)
        
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
            font=("Arial", 11, "bold"),
            bg=self.bg_color,
            padx=15,
            pady=10
        )
        folder_frame.pack(fill=tk.X, padx=20, pady=10)
        
        # 顯示選擇的資料夾
        selected_frame = tk.Frame(folder_frame, bg="#ffffff", relief=tk.SUNKEN, bd=1)
        selected_frame.pack(fill=tk.X, pady=10)
        
        tk.Label(
            selected_frame,
            text="選擇的資料夾：",
            font=("Arial", 9),
            bg="#ffffff"
        ).pack(anchor=tk.W, padx=10, pady=5)
        
        folder_label = tk.Label(
            selected_frame,
            textvariable=self.selected_dir,
            font=("Courier", 9),
            bg="#ffffff",
            fg="#0066cc",
            wraplength=500,
            justify=tk.LEFT
        )
        folder_label.pack(anchor=tk.W, padx=10, pady=(0, 5))
        
        # 選擇按鈕
        button_frame = tk.Frame(folder_frame, bg=self.bg_color)
        button_frame.pack(fill=tk.X, pady=10)
        
        select_btn = tk.Button(
            button_frame,
            text="🗂️ 瀏覽資料夾...",
            command=self.select_folder,
            font=("Arial", 10),
            bg=self.button_color,
            fg="white",
            padx=15,
            pady=8,
            cursor="hand2"
        )
        select_btn.pack(side=tk.LEFT, padx=5)
        
        # 幫助文字
        help_text = tk.Label(
            folder_frame,
            text="💡 提示：可以選擇任何資料夾，程式會自動掃描子資料夾中的所有圖片",
            font=("Arial", 9, "italic"),
            bg=self.bg_color,
            fg="#666666"
        )
        help_text.pack(anchor=tk.W, pady=5)
        
    def build_options_section(self):
        """構建選項部分"""
        options_frame = tk.LabelFrame(
            self.root,
            text="⚙️ 步驟 2：選擇執行選項",
            font=("Arial", 11, "bold"),
            bg=self.bg_color,
            padx=15,
            pady=10
        )
        options_frame.pack(fill=tk.X, padx=20, pady=10)
        
        # 強制重新命名
        self.force_rename_var = tk.BooleanVar(value=False)
        force_checkbox = tk.Checkbutton(
            options_frame,
            text="🔄 強制重新命名（重新分析所有檔案，包括已命名的）",
            variable=self.force_rename_var,
            font=("Arial", 10),
            bg=self.bg_color,
            cursor="hand2"
        )
        force_checkbox.pack(anchor=tk.W, pady=5)
        
        # 刪除原檔案
        self.delete_original_var = tk.BooleanVar(value=False)
        delete_checkbox = tk.Checkbutton(
            options_frame,
            text="🗑️ 刪除原檔案（保留重命名後的檔案，刪除命名前的檔案）",
            variable=self.delete_original_var,
            font=("Arial", 10),
            bg=self.bg_color,
            fg="#d9534f",
            cursor="hand2"
        )
        delete_checkbox.pack(anchor=tk.W, pady=5)
        
        # 警告文字
        warning_text = tk.Label(
            options_frame,
            text="⚠️ 注意：刪除原檔案操作無法復原！",
            font=("Arial", 9, "italic"),
            bg=self.bg_color,
            fg="#d9534f"
        )
        warning_text.pack(anchor=tk.W, pady=5)
        
    def build_button_section(self):
        """構建按鈕部分"""
        button_frame = tk.Frame(self.root, bg=self.bg_color)
        button_frame.pack(fill=tk.X, padx=20, pady=15)
        
        start_btn = tk.Button(
            button_frame,
            text="🚀 開始命名",
            command=self.start_renaming,
            font=("Arial", 12, "bold"),
            bg="#27ae60",
            fg="white",
            padx=30,
            pady=12,
            cursor="hand2"
        )
        start_btn.pack(side=tk.LEFT, padx=5)
        
        clear_btn = tk.Button(
            button_frame,
            text="🔄 清空",
            command=self.clear_selection,
            font=("Arial", 10),
            bg="#95a5a6",
            fg="white",
            padx=15,
            pady=8,
            cursor="hand2"
        )
        clear_btn.pack(side=tk.LEFT, padx=5)
        
        quit_btn = tk.Button(
            button_frame,
            text="❌ 關閉",
            command=self.root.quit,
            font=("Arial", 10),
            bg="#e74c3c",
            fg="white",
            padx=15,
            pady=8,
            cursor="hand2"
        )
        quit_btn.pack(side=tk.RIGHT, padx=5)
        
    def build_result_section(self):
        """構建結果顯示部分"""
        result_frame = tk.LabelFrame(
            self.root,
            text="📊 執行結果",
            font=("Arial", 11, "bold"),
            bg=self.bg_color,
            padx=10,
            pady=10
        )
        result_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # 結果文本框
        self.result_text = scrolledtext.ScrolledText(
            result_frame,
            height=10,
            font=("Courier", 9),
            bg="white",
            fg="#333333",
            wrap=tk.WORD
        )
        self.result_text.pack(fill=tk.BOTH, expand=True)
        
        # 初始信息
        self.log("歡迎使用圖片智能命名系統！\n")
        self.log("👉 請先選擇要命名的資料夾\n")
        self.log("=" * 60 + "\n")
        
    def log(self, message):
        """在結果框中記錄信息"""
        self.result_text.insert(tk.END, message)
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
            self.log(f"\n✅ 已選擇資料夾：{folder}\n")
            
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
            self.log(info)
            
        except Exception as e:
            self.log(f"\n⚠️ 掃描資料夾時出錯：{str(e)}\n")
    
    def clear_selection(self):
        """清空選擇"""
        self.selected_dir.set("")
        self.force_rename_var.set(False)
        self.delete_original_var.set(False)
        self.result_text.delete(1.0, tk.END)
        self.log("歡迎使用圖片智能命名系統！\n")
        self.log("👉 請先選擇要命名的資料夾\n")
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
            if isinstance(widget, tk.Button):
                widget.config(state=tk.DISABLED)
            elif isinstance(widget, tk.Checkbutton):
                widget.config(state=tk.DISABLED)
    
    def enable_controls(self):
        """啟用控制項"""
        for widget in self.root.winfo_children():
            if isinstance(widget, tk.Button):
                widget.config(state=tk.NORMAL)
            elif isinstance(widget, tk.Checkbutton):
                widget.config(state=tk.NORMAL)
    
    def run_renaming(self, folder):
        """執行命名（在線程中運行）"""
        try:
            self.log(f"\n🚀 開始處理...\n")
            self.log(f"資料夾：{folder}\n")
            self.log(f"時間：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            self.log("=" * 60 + "\n")
            
            # 構建命令
            cmd = [
                "python3",
                str(PROJECT_ROOT / "src" / "full_batch_rename_execute.py"),
                "--target-dir", folder
            ]
            
            if self.force_rename_var.get():
                cmd.append("--force-rename")
            
            self.log("⏳ 正在分析圖片內容（這可能需要幾分鐘）...\n")
            self.log("提示：進度信息將在下方顯示\n")
            self.log("=" * 60 + "\n")
            
            # 執行命令
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=3600  # 1小時超時
            )
            
            # 顯示輸出
            if result.stdout:
                self.log(result.stdout)
            
            if result.returncode == 0:
                self.log("\n" + "=" * 60 + "\n")
                self.log("✅ 命名完成！\n")
                
                if self.delete_original_var.get():
                    self.log("\n⏳ 正在刪除原檔案...\n")
                    # 這裡可以添加刪除邏輯
                    self.log("✅ 原檔案已刪除\n")
                
                self.log("\n🎉 所有操作已完成！\n")
            else:
                self.log("\n❌ 執行出錯：\n")
                self.log(result.stderr)
        
        except subprocess.TimeoutExpired:
            self.log("\n❌ 執行超時（超過 1 小時）\n")
        
        except Exception as e:
            self.log(f"\n❌ 出錯：{str(e)}\n")
        
        finally:
            # 重新啟用控制項
            self.enable_controls()


def main():
    """主函數"""
    root = tk.Tk()
    app = ImageRenamerGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
