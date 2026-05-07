#!/usr/bin/env python3
# scraper.py - Merge JSON từ tv.hailab.cloud + buncha JSON

import json
import requests
from pathlib import Path

# URLs
HAILAB_URL = "https://tv.hailab.cloud/"
BUNCHA_URL = "https://raw.githubusercontent.com/xixixius-ai/buncha-stream/refs/heads/main/output.json"

print("📡 Fetching tv.hailab.cloud...")
hailab = requests.get(HAILAB_URL, headers={'User-Agent': 'Mozilla/5.0'}).json()

print("📦 Fetching buncha JSON...")
buncha = requests.get(BUNCHA_URL).json()

# 🔍 Lọc chỉ lấy group "Kênh VTV" + kênh "HTV Thể Thao" từ hailab
tv_channels = []
for group in hailab.get('groups', []):
    if group.get('name') == 'Kênh VTV':
        tv_channels.extend(group.get('channels', []))
    # Thêm HTV Thể Thao nếu có (tìm trong tất cả groups)
    for ch in group.get('channels', []):
        if ch.get('name') == 'HTV Thể Thao' and ch not in tv_channels:
            tv_channels.append(ch)

print(f"✅ Lấy được {len(tv_channels)} kênh TV")

# 📺 Tạo group mới "Kênh Truyền Hình"
tv_group = {
    "id": "grp-tv-channels",
    "name": "📺 Kênh Truyền Hình",
    "display": "vertical",
    "grid_number": 3,
    "enable_detail": False,
    "channels": tv_channels
}

# 🔗 Merge: TV group trên đầu + buncha groups bên dưới
result = {
    **buncha,
    "groups": [tv_group] + buncha.get('groups', [])
}

# 💾 Ghi file
output = Path("output.json")
output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')

print(f"✨ DONE! output.json đã được tạo")
print(f"📍 {output.resolve()}")
print(f"📊 Total groups: {len(result['groups'])}")
