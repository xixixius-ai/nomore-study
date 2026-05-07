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

    # 2. Đọc file hoiquan.json
    with open(cfg["sources"]["tv_json"], "r", encoding="utf-8") as f:
        tv_list = json.load(f)

    # 3. Fetch Buncha gốc
    buncha = requests.get(cfg["sources"]["buncha_json"]).json()

    # 4. Chuyển đổi list kênh sang format Buncha chuẩn
    tv_group = {
        "id": "grp-tv-hoiquan",
        "name": "📺 Kênh Truyền Hình",
        "display": "vertical",
        "grid_number": 2,              # Giống bóng đá/bóng rổ
        "enable_detail": False,
        "channels": [convert_ch(ch, i) for i, ch in enumerate(tv_list)]
    }

    # 5. Merge: Group TV lên đầu
    result = {**buncha, "groups": [tv_group] + buncha.get("groups", [])}

    # 6. Lưu file
    output_path = Path(cfg.get("output", "output.json"))
    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✅ Xong! Đã tạo {output_path} với {len(tv_list)} kênh TV.")

def convert_ch(ch, i):
    """Chuyển đổi chuẩn y hệt format channel của Buncha (Bóng Đá, Bóng Rổ...)"""
    return {
        "id": f"tv-{i}",
        "name": ch["name"],
        "type": "single",
        "display": "thumbnail-only",   # Bắt buộc giống Buncha
        "enable_detail": False,
        "labels": [                    # Phải là mảng []
            {
                "text": "● LIVE",
                "position": "top-left",
                "color": "#00000080",
                "text_color": "#ff4444"
            }
        ],
        "sources": [
            {
                "id": f"src-{i}",
                "name": "BunchaTV",     # Giống hệt Buncha
                "contents": [
                    {
                        "id": f"ct-{i}",
                        "name": ch["name"],
                        "streams": [
                            {
                                "id": f"st-{i}",
                                "name": "KT", # Giống hệt Buncha
                                "stream_links": [
                                    {
                                        "id": f"lnk-{i}",
                                        "name": "Link 1",
                                        "type": "hls",
                                        "default": True,
                                        "url": ch["url"],
                                        "request_headers": [] # Bắt buộc là mảng [], không được để null
                                    }
                                ]
                            }
                        ]
                    }
                ]
            }
        ],
        "image": {                     # Format image chuẩn của Buncha
            "padding": 1,
            "background_color": "#ffffff",
            "display": "contain",
            "url": ch.get("logo", ""),
            "width": 1600,
            "height": 1200
        }
    }

if __name__ == "__main__":
    main()
