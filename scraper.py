#!/usr/bin/env python3
import json
import yaml
import requests
from pathlib import Path

def main():
    print("📂 Đọc dữ liệu nguồn...")
    with open("config.yml", "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    # 1. Đọc file JSON gốc
    with open(cfg["sources"]["tv_json"], "r", encoding="utf-8") as f:
        data = json.load(f)

    # 2. Lọc kênh: Toàn bộ group "Kênh VTV" + kênh "HTV Thể Thao"
    vtv_channels = []
    htv_the_thao = None
    
    for group in data.get("groups", []):
        if group.get("name") == "Kênh VTV":
            vtv_channels.extend(group.get("channels", []))
        for ch in group.get("channels", []):
            if ch.get("name") == "HTV Thể Thao":
                htv_the_thao = ch

    # 3. Ghép danh sách
    selected_channels = vtv_channels[:]
    if htv_the_thao:
        selected_channels.append(htv_the_thao)
        
    print(f"✅ Đã chọn {len(selected_channels)} kênh TV")
    if not selected_channels:
        print("⚠️ Không tìm thấy kênh. Kiểm tra lại file nguồn.")
        return

    # 4. Tạo group mới
    tv_group = {
        "id": "grp-tv-channels",
        "name": "📺 Kênh Truyền Hình",
        "display": "vertical",
        "grid_number": 3,
        "enable_detail": False,
        "channels": selected_channels
    }

    # 5. Fetch Buncha JSON & Merge
    print("📦 Fetching BunchaTV JSON...")
    buncha = requests.get(cfg["sources"]["buncha_json"]).json()
    
    result = {
        **buncha,
        "groups": [tv_group] + buncha.get("groups", [])
    }

    # 6. Lưu output
    output_path = Path("output.json")
    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✨ DONE! Đã lưu: {output_path}")
    print(f"📊 Tổng groups: {len(result['groups'])}")

if __name__ == "__main__":
    main()
