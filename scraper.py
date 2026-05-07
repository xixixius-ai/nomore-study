#!/usr/bin/env python3
import json
import yaml
import requests
from pathlib import Path

# 1. Load config
with open("config.yml", "r", encoding="utf-8") as f:
    cfg = yaml.safe_load(f)

# 2. Đọc hoiquan.json
print(" Reading hoiquan.json...")
tv_data = json.loads(Path(cfg["sources"]["tv_json"]).read_text(encoding="utf-8"))

# 3. Transform sang format app đọc được
channels = []
for i, ch in enumerate(tv_data):
    channels.append({
        "id": f"tv-{i}",
        "name": ch["name"],
        "url": ch["url"],
        "logo": ch.get("logo", ""),
        "type": "single",
        "display": "thumbnail-only",
        "enable_detail": False,
        "labels": [{"text": "● LIVE", "position": "top-left", "color": "#00000080", "text_color": "#ff4444"}],
        "request_headers": [
            {"key": "Referer", "value": "https://xem.hoiquan.click/"},
            {"key": "User-Agent", "value": "Mozilla/5.0"}
        ]
    })

print(f"✅ Đã chuẩn bị {len(channels)} kênh TV")

# 4. Fetch buncha JSON gốc
print("📦 Fetching buncha JSON...")
buncha = requests.get(cfg["sources"]["buncha_json"]).json()

# 5. Tạo group TV & Merge (TV group luôn ở vị trí đầu)
tv_group = {
    "id": cfg["tv_group"]["id"],
    "name": cfg["tv_group"]["name"],
    "display": cfg["tv_group"]["display"],
    "grid_number": cfg["tv_group"]["grid_number"],
    "enable_detail": cfg["tv_group"]["enable_detail"],
    "channels": channels
}

result = {
    **buncha,
    "groups": [tv_group] + buncha.get("groups", [])
}

# 6. Ghi ra output.json
output_path = Path("output.json")
output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

print(f"✨ DONE! File output.json đã được tạo")
print(f"📍 {output_path.resolve()}")
print(f"📊 Total groups: {len(result['groups'])}")
