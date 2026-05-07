import json
import requests
import yaml
from pathlib import Path

def load_config():
    with open("config.yml", "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def extract_channels(data, cfg):
    selected = []
    target_group = cfg["filters"]["group_name"]
    target_channel = cfg["filters"]["channel_name"]

    for group in data.get("groups", []):
        if group.get("name") == target_group:
            selected.extend(group.get("channels", []))
        for ch in group.get("channels", []):
            if ch.get("name") == target_channel and ch not in selected:
                selected.append(ch)
    return selected

def main():
    cfg = load_config()
    print("📂 Đọc dữ liệu nguồn...")

    with open(cfg["sources"]["input_json"], "r", encoding="utf-8") as f:
        source_data = json.load(f)

    tv_channels = extract_channels(source_data, cfg)
    print(f"✅ Đã lấy được {len(tv_channels)} kênh TV")

    if not tv_channels:
        print("❌ Không tìm thấy kênh. Kiểm tra lại file nguồn.")
        return

    new_group = {
        "id": cfg["tv_group"]["id"],
        "name": cfg["tv_group"]["name"],
        "display": cfg["tv_group"]["display"],
        "grid_number": cfg["tv_group"]["grid_number"],
        "enable_detail": cfg["tv_group"]["enable_detail"],
        "channels": tv_channels
    }

    print("📦 Fetching BunchaTV JSON...")
    buncha = requests.get(cfg["sources"]["buncha_url"]).json()

    result = {
        **buncha,
        "groups": [new_group] + buncha.get("groups", [])
    }

    output_path = Path("output.json")
    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✨ DONE! Đã lưu vào {output_path}")
    print(f"📊 Tổng groups: {len(result['groups'])}")

if __name__ == "__main__":
    main()
