#!/usr/bin/env python3
import json
import re
import yaml
from pathlib import Path
import requests

# Load config
with open("config.yml", "r", encoding="utf-8") as f:
    cfg = yaml.safe_load(f)

# Đọc M3U
m3u = Path(cfg["sources"]["m3u_file"]).read_text(encoding="utf-8")

# Parse channels từ M3U
channels = []
lines = [l.strip() for l in m3u.split("\n") if l.strip()]
current = None

for line in lines:
    if line.startswith("#EXTINF:"):
        name = re.search(r",(.+)$", line)
        name = name.group(1).strip() if name else ""
        logo = re.search(r'tvg-logo="([^"]*)"', line)
        logo = logo.group(1) if logo else ""
        group = re.search(r'group-title="([^"]*)"', line)
        group = group.group(1) if group else "Uncategorized"
        current = {"name": name, "logo": logo, "group": group}
    elif line.startswith("http") and current:
        # Lọc chỉ lấy VTV và HTV Thể Thao
        if current["group"] == "Kênh VTV" or current["name"] == "HTV Thể Thao":
            channels.append({
                "id": f"tv-{len(channels)}",
                "name": current["name"],
                "url": line,
                "logo": current["logo"]
            })
        current = None

# Tạo TV group
tv_group = {
    "id": "grp-tv-channels",
    "name": "📺 Kênh Truyền Hình",
    "display": "vertical",
    "grid_number": 3,
    "enable_detail": False,
    "channels": channels
}

print(f"✅ Lấy được {len(channels)} kênh TV")

# Fetch buncha JSON
print("📦 Fetching buncha JSON...")
buncha = requests.get(cfg["sources"]["buncha_json"]).json()

# Merge: TV group trên đầu + buncha groups bên dưới
result = {
    **buncha,
    "groups": [tv_group] + buncha.get("groups", [])
}

# Ghi file
with open("output.json", "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

print(f"✨ DONE! File output.json đã được tạo ({len(result['groups'])} groups)")
print(f"📍 Vị trí: {Path('output.json').resolve()}")
