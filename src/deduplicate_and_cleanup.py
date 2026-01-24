#!/usr/bin/env python3
"""
第一步：偵測並清理重複圖片
使用文件內容哈希確保準確的重複偵測
"""

import hashlib
import json
from pathlib import Path
from collections import defaultdict

downloads_dir = Path("/Users/hsiaojohnny/Downloads")
session_dir = Path("/Users/hsiaojohnny/.copilot/session-state/0627c76d-21e0-4128-b7ff-ea283b16e7d2")

print("🔍 第一步：偵測重複圖片檔案")
print("=" * 70)
print()

# 掃描所有圖片
image_files = []
for file_path in sorted(downloads_dir.glob("*")):
    if file_path.is_file() and file_path.suffix.lower() in {'.png', '.jpg', '.jpeg', '.webp', '.gif'}:
        image_files.append(file_path)

print(f"📋 掃描完成：{len(image_files)} 個圖片檔案")
print()

# 計算檔案哈希值
print("🔐 計算檔案哈希值...")
file_hashes = defaultdict(list)

for file_path in image_files:
    try:
        # 計算文件內容的 MD5 哈希
        md5_hash = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                md5_hash.update(chunk)
        
        file_hash = md5_hash.hexdigest()
        file_hashes[file_hash].append(file_path)
    except:
        pass

print(f"✅ 哈希計算完成")
print()

# 找出重複檔案
duplicates_to_delete = []
duplicate_info = []

for file_hash, files in file_hashes.items():
    if len(files) > 1:
        # 按修改時間排序，保留最新的，刪除舊的
        sorted_files = sorted(files, key=lambda x: x.stat().st_mtime, reverse=True)
        
        # 保留第一個（最新的），其他標記為重複
        for dup_file in sorted_files[1:]:
            duplicates_to_delete.append(dup_file)
            duplicate_info.append({
                "keep": sorted_files[0].name,
                "delete": dup_file.name,
                "hash": file_hash,
                "size": dup_file.stat().st_size
            })

print(f"📊 重複偵測結果:")
print(f"  總計檔案：{len(image_files)}")
print(f"  唯一檔案：{len(image_files) - len(duplicates_to_delete)}")
print(f"  重複副本：{len(duplicates_to_delete)}")
print()

if duplicates_to_delete:
    print("🗑️ 要刪除的重複檔案清單：")
    print()
    for info in duplicate_info[:10]:  # 顯示前10個
        print(f"  保留: {info['keep']}")
        print(f"  刪除: {info['delete']}")
        print()
    
    if len(duplicate_info) > 10:
        print(f"  ... 還有 {len(duplicate_info) - 10} 個重複")
    
    print()
    print("開始刪除重複檔案...")
    
    deleted_count = 0
    for dup_file in duplicates_to_delete:
        try:
            dup_file.unlink()
            deleted_count += 1
            print(f"  ✅ 已刪除: {dup_file.name}")
        except Exception as e:
            print(f"  ❌ 刪除失敗: {dup_file.name} - {e}")
    
    print()
    print(f"✅ 成功刪除：{deleted_count} 個重複檔案")
else:
    print("✅ 沒有發現重複檔案")

# 保存清理報告
cleanup_report = {
    "original_count": len(image_files),
    "duplicates_found": len(duplicates_to_delete),
    "remaining_count": len(image_files) - len(duplicates_to_delete),
    "duplicate_details": duplicate_info
}

with open(session_dir / "cleanup_report.json", "w", encoding="utf-8") as f:
    json.dump(cleanup_report, f, ensure_ascii=False, indent=2)

print()
print("=" * 70)
print(f"✅ 清理完成")
print(f"📊 最終結果：")
print(f"   原始檔案數：{cleanup_report['original_count']}")
print(f"   已刪除：{cleanup_report['duplicates_found']}")
print(f"   保留檔案數：{cleanup_report['remaining_count']}")
