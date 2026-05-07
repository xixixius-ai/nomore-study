#!/usr/bin/env python3
import json, yaml, requests
from pathlib import Path

cfg = yaml.safe_load(Path("config.yml").read_text(encoding="utf-8"))
tv_list = json.loads(Path(cfg["sources"]["tv_json"]).read_text(encoding="utf-8"))
buncha = requests.get(cfg["sources"]["buncha_json"]).json()

# Transform sang format MON Player cần
def fmt(ch, i):
    return {
        "id": f"tv-{i}", "name": ch["name"], "description": "",
        "label": {"text": "Trực Tiếp", "position": "top-left", "color": "#f70525", "text_color": "#ffffff"},
        "image": {"url": ch.get("logo",""), "type": "cover", "width": 640, "height": 480},
        "grid_number": 1, "display": "text-below", "type": "single", "enable_detail": True,
        "sources": [{"id": f"s-{i}", "name": "src", "image": None, "contents": [{
            "id": f"c-{i}", "name": "cnt", "image": None, "streams": [{
                "id": f"st-{i}", "name": "Live", "image": {"url": ch.get("logo",""), "type": "cover"},
                "stream_links": [{"id": f"l-{i}", "name": "Link 1", "url": ch["url"], "type": "hls",
                    "default": True, "subtitles": None, "remote_data": None, "request_headers": [
                        {"key": "Referer", "value": "https://xem.hoiquan.click/"},
                        {"key": "User-Agent", "value": "Mozilla/5.0"}]}]}]}], "remote_data": None}]}

tv_group = {**cfg["tv_group"], "channels": [fmt(ch,i) for i,ch in enumerate(tv_list)]}
result = {**buncha, "groups": [tv_group] + buncha.get("groups", [])}
Path("output.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"✅ Done: {len(tv_list)} TV channels + {len(buncha['groups'])} buncha groups")
