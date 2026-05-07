#!/usr/bin/env python3
import json
import yaml
import requests
from pathlib import Path

def main():
    print("⏳ Đang xử lý...")
    
    # 1. Đọc config
    with open("config.yml", "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    # 2. Đọc file hoiquan.json (Đã lọc sẵn)
    with open(cfg["sources"]["tv_json"], "r", encoding="utf-8") as f:
        tv_list = json.load(f)

    # 3. Fetch Buncha gốc
    buncha = requests.get(cfg["sources"]["buncha_json"]).json()

    # 4. Chuyển đổi list kênh sang format Buncha (để click là chạy)
    tv_group = {
        "id": "grp-tv-channels",
        "name": "📺 Kênh Truyền Hình",
        "display": "vertical",
        "grid_number": 3,
        "enable_detail": False, # ✅ False để click thumbnail là vào xem luôn
        "channels": [convert_ch(ch, i) for i, ch in enumerate(tv_list)]
    }

    # 5. Merge: Group TV lên đầu, Buncha ở dưới
    result = {**buncha, "groups": [tv_group] + buncha.get("groups", [])}

    # 6. Lưu file
    output_path = Path("output.json")
    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✅ Xong! Đã tạo {output_path} với {len(tv_list)} kênh TV.")

def convert_ch(ch, i):
    """Chuyển object đơn giản {name, url, logo} sang format chuẩn App"""
    return {
        "id": f"tv-{i}",
        "name": ch["name"],
        "description": "",
        "label": {"text": "Trực Tiếp", "position": "top-left", "color": "#f70525", "text_color": "#ffffff"},
        "image": {"url": ch.get("logo", ""), "type": "cover", "width": 640, "height": 480},
        "grid_number": 1,
        "display": "text-below",
        "type": "single",
        "enable_detail": False,
        "sources": [{
            "id": f"s-{i}", "name": "src", "image": None,
            "contents": [{
                "id": f"c-{i}", "name": "cnt", "image": None,
                "streams": [{
                    "id": f"st-{i}", "name": "Live", "image": {"url": ch.get("logo", ""), "type": "cover"},
                    "stream_links": [{
                        "id": f"l-{i}", "name": "Link 1", "url": ch["url"], "type": "hls",
                        "default": True, "subtitles": None, "remote_data": None, "request_headers": None
                    }]
                }]
            }]
        }]
    }

if __name__ == "__main__":
    main()
