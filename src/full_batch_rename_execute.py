#!/usr/bin/env python3
"""
完整執行：使用 Qwen3-VL 進行全量圖片分析和精準重命名

流程：
1. 分析全部圖片
2. 生成精準命名對照表
3. 執行檔案重命名
4. 生成詳細報告

新增功能（v1.1）：
- 增量模式（默認）：跳過已命名的檔案（檔名包含中文）
- 強制重新命名模式：重新分析和命名所有檔案
- 全局檔案追蹤機制
"""

import os
import json
import base64
import requests
from pathlib import Path
from typing import Dict, List, Optional
import time
from datetime import datetime
import argparse
import sys

# 導入進度追蹤器
from progress_tracker import ProgressTracker

# 配置
# 使用相對路徑：PROJECT_ROOT 應該是執行腳本的目錄
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
LOGS_DIR = PROJECT_ROOT / "logs"
SESSION_DIR = DATA_DIR / "session"

LM_STUDIO_API = "http://127.0.0.1:1234/v1/chat/completions"
BATCH_SIZE = 10  # 每批 10 張圖片

# 確保必要的目錄存在
DATA_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)
SESSION_DIR.mkdir(parents=True, exist_ok=True)

# 解析命令行參數
parser = argparse.ArgumentParser(
    description="圖片智能命名系統 - 使用 Qwen3-VL 進行視覺分析和重命名"
)
parser.add_argument(
    "--force-rename",
    "--override",
    dest="force_rename",
    action="store_true",
    help="強制重新命名已命名的檔案（增量模式）"
)
parser.add_argument(
    "--target-dir",
    default=None,
    help="指定要處理的目錄（默認：使用交互式提示輸入）"
)
parser.add_argument(
    "--limit",
    type=int,
    default=None,
    help="限制處理的圖片數量（用於測試，默認：無限制）"
)
parser.add_argument(
    "--delete-original",
    action="store_true",
    help="重命名後刪除原檔案"
)
args = parser.parse_args()

FORCE_RENAME = args.force_rename
LIMIT_IMAGES = args.limit  # 新增：限制圖片數量
DELETE_ORIGINAL = args.delete_original  # 新增：是否刪除原檔案

# 如果沒有指定目錄，使用交互式輸入或當前目錄
if args.target_dir:
    TARGET_DIR = Path(args.target_dir).expanduser()
else:
    # 默認為當前工作目錄
    TARGET_DIR = Path.cwd()

print("=" * 80)
print("🚀 圖片智能命名系統 - Qwen3-VL 批量分析和重命名 v1.2")
print("=" * 80)
print(f"時間：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"目標目錄：{TARGET_DIR}")
if FORCE_RENAME:
    print("📌 模式：強制重新命名（將重新分析所有檔案）")
else:
    print("📌 模式：增量模式（將跳過已命名的檔案）")
print()

# 初始化進度追蹤器
progress = ProgressTracker(SESSION_DIR, "rename")

def is_already_renamed(filename: str) -> bool:
    """檢測檔案是否已被命名（檔名包含中文字符）"""
    import re
    return bool(re.search(r'[\u4e00-\u9fff]', filename))

# 掃描所有圖片（遞迴掃描所有子資料夾）
image_files = sorted([
    f for f in TARGET_DIR.rglob("*") 
    if f.is_file() and f.suffix.lower() in {'.png', '.jpg', '.jpeg', '.webp', '.gif', '.bmp'}
])

# 應用限制（用於測試）
if LIMIT_IMAGES:
    image_files = image_files[:LIMIT_IMAGES]

print(f"📊 掃描結果：找到 {len(image_files)} 個圖片檔案", end="")
if LIMIT_IMAGES:
    print(f"（已限制為 {LIMIT_IMAGES} 張用於測試）")
else:
    print()

# 檢測已命名和未命名的檔案
if not FORCE_RENAME:
    renamed_files = [f for f in image_files if is_already_renamed(f.stem)]
    unnamed_files = [f for f in image_files if not is_already_renamed(f.stem)]
    
    print(f"   已命名：{len(renamed_files)} 個")
    print(f"   未命名：{len(unnamed_files)} 個")
    
    if renamed_files:
        print(f"   💡 提示：已命名的檔案將被跳過。使用 --force-rename 重新分析所有檔案")
    
    # 增量模式：只處理未命名的檔案
    image_files = unnamed_files
    print()
    print(f"⚙️  開始處理 {len(image_files)} 個未命名的檔案...")
else:
    print(f"   批次大小：{BATCH_SIZE} 張/批")
    print(f"   預計批次數：{(len(image_files) + BATCH_SIZE - 1) // BATCH_SIZE}")
    print()

print()

# 分析結果儲存
analysis_results = []
failed_files = []
skipped_duplicates = []

def encode_image_to_base64(image_path: Path) -> str:
    """將圖片編碼為 base64"""
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode('utf-8')

def get_image_media_type(image_path: Path) -> str:
    """根據副檔名確定 MIME 類型"""
    ext = image_path.suffix.lower()
    return {
        '.png': 'image/png',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.webp': 'image/webp',
        '.gif': 'image/gif'
    }.get(ext, 'image/png')

def analyze_image_with_qwen(image_path: Path, retry_count: int = 3) -> Dict:
    """使用 Qwen3-VL 分析單張圖片（含重試機制）"""
    
    for attempt in range(retry_count):
        try:
            # 編碼圖片
            image_base64 = encode_image_to_base64(image_path)
            media_type = get_image_media_type(image_path)
            
            # 準備分析提示
            analysis_prompt = """請深度分析這張圖片並用台灣繁體中文回答。返回 JSON 格式的結果（只返回 JSON，不要其他文字）：

{
  "image_title": "圖片中的標題文字（如無標題則為 'N/A'）",
  "main_theme": "核心主題分類（如：財經、技術、設計、報告等）",
  "sub_theme": "子分類（如：投資分析、AI系統、創意設計等）",
  "core_content": "圖片的具體核心內容（關鍵詞或短句，20字以內）",
  "recommended_name": "推薦命名（格式：主題_子主題_具體標題，最多25字，不含日期）"
}"""
            
            # 調用 LM Studio API
            headers = {"Content-Type": "application/json"}
            
            payload = {
                "model": "qwen/qwen3-vl-30b",
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:{media_type};base64,{image_base64}"
                                }
                            },
                            {
                                "type": "text",
                                "text": analysis_prompt
                            }
                        ]
                    }
                ],
                "temperature": 0.3,
                "max_tokens": 500
            }
            
            response = requests.post(LM_STUDIO_API, json=payload, headers=headers, timeout=60)
            response.raise_for_status()
            
            # 解析回應
            result = response.json()
            analysis_text = result['choices'][0]['message']['content']
            
            # 提取 JSON
            try:
                analysis_json = json.loads(analysis_text)
            except json.JSONDecodeError:
                import re
                json_match = re.search(r'\{.*\}', analysis_text, re.DOTALL)
                if json_match:
                    analysis_json = json.loads(json_match.group())
                else:
                    raise ValueError(f"無法解析回應")
            
            return {
                "filename": str(image_path.relative_to(TARGET_DIR)),
                "status": "success",
                "analysis": analysis_json
            }
        
        except Exception as e:
            if attempt < retry_count - 1:
                time.sleep(2)  # 重試前等待
                continue
            else:
                return {
                    "filename": str(image_path.relative_to(TARGET_DIR)),
                    "status": "error",
                    "error": str(e)
                }

# 加載之前的結果（如果有）
previous_results_file = SESSION_DIR / "qwen_vision_analysis_sample.json"
if previous_results_file.exists():
    print("📂 加載之前的樣本分析結果...")
    with open(previous_results_file, 'r', encoding='utf-8') as f:
        previous = json.load(f)
        analysis_results = previous.get('detailed_results', [])
    print(f"   已加載 {len(analysis_results)} 個結果")
    processed_files = {r['filename'] for r in analysis_results}
    remaining_files = [f for f in image_files if f.name not in processed_files]
    print(f"   剩餘待分析：{len(remaining_files)} 張")
    print()
else:
    remaining_files = image_files
    processed_files = set()

# 批量處理圖片
print("🚀 開始全量分析...")
print()

total_processed = len(analysis_results)
successful = sum(1 for r in analysis_results if r['status'] == 'success')
failed = sum(1 for r in analysis_results if r['status'] != 'success')

for batch_idx in range((len(remaining_files) + BATCH_SIZE - 1) // BATCH_SIZE):
    start_idx = batch_idx * BATCH_SIZE
    end_idx = min(start_idx + BATCH_SIZE, len(remaining_files))
    
    batch_files = remaining_files[start_idx:end_idx]
    batch_num = len(analysis_results) // BATCH_SIZE + batch_idx + 1
    
    # 更新進度追蹤
    progress.update_analysis(batch_num, BATCH_SIZE, total_processed)
    
    for img_idx, img_file in enumerate(batch_files, 1):
        print(f"   [{img_idx}/{len(batch_files)}] {img_file.name[:45]}... ", end="", flush=True)
        
        result = analyze_image_with_qwen(img_file)
        analysis_results.append(result)
        total_processed += 1
        
        if result['status'] == 'success':
            successful += 1
            print(f"✅")
        else:
            failed += 1
            failed_files.append(result)
            print(f"❌")
        
        # 計算並輸出進度百分比
        progress_pct = int(total_processed * 100 / len(remaining_files)) if remaining_files else 0
        eta = progress.get_eta_seconds()
        eta_str = progress._format_time(eta) if eta > 0 else "計算中..."
        print(f"[進度] 分析: {progress_pct}% | {total_processed}/{len(remaining_files)} | ETA: {eta_str}", flush=True)
        
        # 稍作延遲
        time.sleep(0.5)
    
    print()
    
    # 每批後保存一次（以防中斷）
    temp_file = SESSION_DIR / f"qwen_analysis_progress.json"
    with open(temp_file, 'w', encoding='utf-8') as f:
        json.dump({
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "total_processed": total_processed,
                "successful": successful,
                "failed": failed,
            },
            "results": analysis_results
        }, f, ensure_ascii=False, indent=2)

print("=" * 80)
print(f"✨ 分析完成：{datetime.now().strftime('%H:%M:%S')}")
print("=" * 80)
print(f"總計：{total_processed} 張圖片")
print(f"成功：{successful} 張 ✅")
print(f"失敗：{failed} 張 ❌")
print()

# 更新進度：完成分析
progress.complete_analysis(successful, failed)

# 保存完整分析結果
with open(SESSION_DIR / "qwen_vision_analysis_complete.json", "w", encoding="utf-8") as f:
    json.dump({
        "metadata": {
            "timestamp": datetime.now().isoformat(),
            "total_analyzed": total_processed,
            "successful": successful,
            "failed": failed,
            "api_endpoint": LM_STUDIO_API,
            "model": "qwen/qwen3-vl-30b"
        },
        "detailed_results": analysis_results
    }, f, ensure_ascii=False, indent=2)

print(f"💾 完整分析結果已保存：")
print(f"   {SESSION_DIR / 'qwen_vision_analysis_complete.json'}")
print()

# 生成命名對照表和重命名計畫
print("�� 生成重命名對照表...")

rename_plan = []
for result in analysis_results:
    if result['status'] == 'success':
        old_name = result['filename']
        analysis = result['analysis']
        new_name = analysis.get('recommended_name', 'UNKNOWN')
        
        # 確保新名稱有副檔名
        old_path = TARGET_DIR / old_name
        ext = old_path.suffix
        if not new_name.endswith(ext):
            new_name = new_name + ext
        
        rename_plan.append({
            "old_filename": old_name,
            "new_filename": new_name,
            "image_title": analysis.get('image_title', 'N/A'),
            "main_theme": analysis.get('main_theme', 'N/A'),
            "sub_theme": analysis.get('sub_theme', 'N/A'),
            "core_content": analysis.get('core_content', 'N/A')
        })

# 檢查重複的新名稱
name_counts = {}
for item in rename_plan:
    new_name = item['new_filename']
    name_counts[new_name] = name_counts.get(new_name, 0) + 1

duplicates = {k: v for k, v in name_counts.items() if v > 1}
if duplicates:
    print(f"⚠️  警告：檢測到 {len(duplicates)} 個重複的新名稱")
    # 為重複的名稱添加序號
    new_name_count = {}
    for item in rename_plan:
        new_name = item['new_filename']
        if new_name in duplicates:
            new_name_count[new_name] = new_name_count.get(new_name, 0) + 1
            base, ext = new_name.rsplit('.', 1)
            item['new_filename'] = f"{base}_{new_name_count[new_name]:02d}.{ext}"

# 保存對照表
with open(SESSION_DIR / "qwen_rename_plan_complete.json", "w", encoding="utf-8") as f:
    json.dump(rename_plan, f, ensure_ascii=False, indent=2)

print(f"✅ 已為 {len(rename_plan)} 個文件生成新名稱")
print(f"📊 對照表已保存：{SESSION_DIR / 'qwen_rename_plan_complete.json'}")
print()

# 執行重命名
print("🔄 開始執行重命名...")
print()

# 檢查是否有需要重命名的檔案
if not rename_plan:
    print("[完成] ℹ️ 沒有找到需要重命名的圖片")
    print("[完成] ✅ 所有操作已完成！", flush=True)
    print()
else:
    # 更新進度：開始重命名
    progress.start_rename()

    renamed_count = 0
    deleted_count = 0
    rename_errors = []
    delete_errors = []

    for idx, item in enumerate(rename_plan, 1):
        old_path = TARGET_DIR / item['old_filename']
        new_path = TARGET_DIR / item['new_filename']
        
        try:
            if old_path.exists():
                if new_path.exists() and new_path != old_path:
                    # 避免覆蓋現有檔案
                    base, ext = new_path.name.rsplit('.', 1)
                    counter = 1
                    while new_path.exists():
                        new_path = TARGET_DIR / f"{base}_{counter:02d}.{ext}"
                        counter += 1
                    item['new_filename'] = new_path.name
                
                # 如果勾選了「刪除原檔案」，先記錄舊檔案路徑和內容
                should_delete_after_rename = DELETE_ORIGINAL
                
                # 執行重命名（這會將 old_path 更名為 new_path）
                old_path.rename(new_path)
                renamed_count += 1
                print(f"✅ {item['old_filename'][:40]:<40} → {new_path.name[:35]}")
                
                # ⚠️ 注意：rename() 之後，old_path 不再存在
                # 所以不需要再次刪除 old_path
                # 如果 should_delete_after_rename，那麼原檔案已經被替換為新檔案了
                # 不需要額外操作
                
                if should_delete_after_rename:
                    deleted_count += 1
                
                # 計算並輸出進度百分比
                progress_pct = int(renamed_count * 100 / len(rename_plan)) if rename_plan else 0
                eta = progress.get_eta_seconds()
                eta_str = progress._format_time(eta) if eta > 0 else "計算中..."
                print(f"[進度] 重命名: {progress_pct}% | {renamed_count}/{len(rename_plan)} | ETA: {eta_str}", flush=True)
                
                # 更新進度
                progress.update_rename(idx)
        
        except Exception as e:
            rename_errors.append({
                "old": item['old_filename'],
                "new": item['new_filename'],
                "error": str(e)
            })
            print(f"❌ {item['old_filename'][:40]:<40} (錯誤：{str(e)[:30]})")

print()
print("=" * 80)
print(f"✨ 重命名完成")
print("=" * 80)

if rename_plan:
    # 更新進度：完成重命名
    progress.complete_rename(renamed_count, len(rename_errors))
    print(f"成功重命名：{renamed_count} 張")
    print(f"重命名失敗：{len(rename_errors)} 張")
    if DELETE_ORIGINAL:
        print(f"✅ 已刪除原檔案（重命名時自動刪除）：{deleted_count} 張")
else:
    renamed_count = 0
    deleted_count = 0
    rename_errors = []

print()

# 輸出最終完成訊息（確保 GUI 能看到）
print("[完成] ✅ 所有操作已完成！", flush=True)
print(f"[完成] 📊 統計：共處理 {total_processed} 張圖片", flush=True)
print(f"[完成] ⏱️  總耗時：{progress._format_time(time.time() - progress.start_time)}", flush=True)
print()

# 保存最終報告
final_report = {
    "timestamp": datetime.now().isoformat(),
    "total_images": len(image_files),
    "analyzed": total_processed,
    "successful_analysis": successful,
    "failed_analysis": failed,
    "renamed": renamed_count,
    "rename_errors": len(rename_errors),
    "deleted": deleted_count if DELETE_ORIGINAL else 0,
    "errors": rename_errors if rename_errors else []
}

with open(SESSION_DIR / "qwen_rename_final_report.json", "w", encoding="utf-8") as f:
    json.dump(final_report, f, ensure_ascii=False, indent=2)

print(f"📝 最終報告已保存：{SESSION_DIR / 'qwen_rename_final_report.json'}")

