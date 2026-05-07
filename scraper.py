#!/usr/bin/env python3
# scraper.py - Parse M3U + Merge BunchaTV + Chỉ ghi file nếu có thay đổi

import json
import re
import yaml
import sys
from pathlib import Path
import requests

CONFIG_PATH = Path("config.yml")
OUTPUT_PATH = Path("output.json")

def load_config() -> dict:
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def fetch_text(url_or_path: str) -> str:
    p = Path(url_or_path)
    if p.exists() and p.is_file():
        return p.read_text(encoding='utf-8')
    return requests.get(url_or_path, headers={'User-Agent': 'Mozilla/5.0'}, timeout=30).text

def parse_m3u_channels(content: str) -> list:
    lines = [l.strip() for l in content.split('\n') if l.strip()]
    channels, current = [], None
    for line in lines:
        if line.startswith('#EXTINF:'):
            name = re.search(r',(.+)$', line)
            attrs = dict(re.findall(r'(\w+(?:-\w+)*)="([^"]*)"', line))
            current = {'name': name.group(1).strip() if name else '', **attrs}
        elif line.startswith('http') and current:
            channels.append({
                'name': current.get('name', ''),
                'url': line,
                'logo': current.get('tvg-logo', ''),
                'group': current.get('group-title', 'Uncategorized'),
                'tvg_id': current.get('tvg-id', '')
            })
            current = None
    return channels

def filter_channels(channels: list, filters: dict) -> list:
    allowed_grp = filters.get('allowed_groups', [])
    allowed_nm = filters.get('allowed_names', [])
    out = []
    for ch in channels:
        if allowed_nm and ch['name'] in allowed_nm:
            out.append(ch)
        elif allowed_grp and ch['group'] in allowed_grp:
            out.append(ch)
    return out

def build_channel(ch: dict, idx: int, cfg: dict) -> dict:
    defa = cfg.get('channel_defaults', {})
    entry = {
        'id': f"tv-{ch['tvg_id'] or idx}" if ch['tvg_id'] else f"tv-{idx}",
        'name': ch['name'],
        'url': ch['url'],
        'logo': ch['logo'],
        'group': ch['group'],
        **{k: v for k, v in defa.items() if k != 'add_live_label' and k != 'add_referer_header' and k != 'referer_url'}
    }
    if defa.get('add_live_label'):
        entry['labels'] = [{'text': '● LIVE', 'position': 'top-left', 'color': '#00000080', 'text_color': '#ff4444'}]
    if defa.get('add_referer_header'):
        entry['request_headers'] = [
            {'key': 'Referer', 'value': defa.get('referer_url', '')},
            {'key': 'User-Agent', 'value': 'Mozilla/5.0'}
        ]
    return entry

def merge_data(tv_channels: list, cfg: dict, base_data: dict) -> dict:
    tv_grp = {
        'id': cfg['tv_group']['id'],
        'name': cfg['tv_group']['name'],
        'display': cfg['tv_group'].get('display', 'vertical'),
        'grid_number': cfg['tv_group'].get('grid_number', 3),
        'enable_detail': cfg['tv_group'].get('enable_detail', False),
        'channels': [build_channel(ch, i, cfg) for i, ch in enumerate(tv_channels)]
    }
    return {**base_data, 'groups': [tv_grp] + base_data.get('groups', [])}

def has_changes(new_data: dict) -> bool:
    """So sánh JSON mới với file cũ, trả True nếu khác biệt"""
    if not OUTPUT_PATH.exists():
        return True
    try:
        old_text = OUTPUT_PATH.read_text(encoding='utf-8')
        # Normalize để so sánh chính xác (giữ nguyên thứ tự mảng)
        return json.loads(old_text) != new_data
    except Exception:
        return True

def main():
    print("🚀 Starting scraper...")
    cfg = load_config()
    
    m3u_content = fetch_text(cfg['sources']['m3u_file'])
    all_ch = parse_m3u_channels(m3u_content)
    filtered = filter_channels(all_ch, cfg['filters'])
    print(f"✅ Selected {len(filtered)}/{len(all_ch)} channels")
    
    base_json = json.loads(fetch_text(cfg['sources']['buncha_json']))
    new_data = merge_data(filtered, cfg, base_json)
    
    if not has_changes(new_data):
        print("📦 No changes detected. Skipping file update.")
        sys.exit(0)
        
    OUTPUT_PATH.write_text(json.dumps(new_data, ensure_ascii=False, indent=2), encoding='utf-8')
    print("🔄 Changes detected. output.json updated successfully.")
    sys.exit(1)  # Exit code 1 để workflow biết cần commit

if __name__ == "__main__":
    main()
