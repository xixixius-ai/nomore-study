#!/usr/bin/env python3
# scraper.py - Parse M3U + Merge BunchaTV + Chỉ ghi file nếu có thay đổi

import json
import re
import yaml
import sys
import hashlib
from pathlib import Path
import requests

CONFIG_PATH = Path("config.yml")
OUTPUT_PATH = Path("output.json")

def load_config() -> dict:
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def fetch_text(url_or_path: str) -> str:
    """Fetch content: hỗ trợ cả file local và URL"""
    p = Path(url_or_path)
    if p.exists() and p.is_file():
        return p.read_text(encoding='utf-8')
    return requests.get(url_or_path, headers={'User-Agent': 'Mozilla/5.0'}, timeout=30).text

def parse_m3u_channels(content: str) -> list:
    """Parse M3U content → list channels"""
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
    """Lọc kênh theo allowed_groups và allowed_names"""
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
    """Build channel object chuẩn app đọc được"""
    defa = cfg.get('channel_defaults', {})
    entry = {
        'id': f"tv-{ch['tvg_id'] or idx}" if ch['tvg_id'] else f"tv-{idx}",
        'name': ch['name'],
        'url': ch['url'],
        'logo': ch['logo'],
        'group': ch['group'],
    }
    # Add defaults
    for k in ['type', 'display', 'enable_detail']:
        if k in defa:
            entry[k] = defa[k]
    # Add live label
    if defa.get('add_live_label'):
        entry['labels'] = [{'text': '● LIVE', 'position': 'top-left', 'color': '#00000080', 'text_color': '#ff4444'}]
    # Add headers
    if defa.get('add_referer_header') and defa.get('referer_url'):
        entry['request_headers'] = [
            {'key': 'Referer', 'value': defa['referer_url']},
            {'key': 'User-Agent', 'value': 'Mozilla/5.0'}
        ]
    return entry

def merge_data(tv_channels: list, cfg: dict, base_data: dict) -> dict:
    """Merge TV group vào đầu danh sách groups"""
    tv_grp = {
        'id': cfg['tv_group']['id'],
        'name': cfg['tv_group']['name'],
        'display': cfg['tv_group'].get('display', 'vertical'),
        'grid_number': cfg['tv_group'].get('grid_number', 3),
        'enable_detail': cfg['tv_group'].get('enable_detail', False),
        'channels': [build_channel(ch, i, cfg) for i, ch in enumerate(tv_channels)]
    }
    return {**base_data, 'groups': [tv_grp] + base_data.get('groups', [])}

def get_file_hash(filepath: Path) -> str:
    """Tính hash của file để so sánh nhanh"""
    if not filepath.exists():
        return ""
    content = filepath.read_bytes()
    return hashlib.md5(content).hexdigest()

def main():
    print("🚀 Starting scraper...")
    
    # Load config
    cfg = load_config()
    
    # 1. Đọc & parse M3U
    print(f"📂 Reading {cfg['sources']['m3u_file']}...")
    m3u_content = fetch_text(cfg['sources']['m3u_file'])
    all_ch = parse_m3u_channels(m3u_content)
    
    # 2. Filter channels
    print("🔍 Filtering channels...")
    filtered = filter_channels(all_ch, cfg['filters'])
    print(f"✅ Selected {len(filtered)}/{len(all_ch)} channels")
    if not filtered:
        print("⚠️ Warning: No channels matched your filters! Check config.yml")
    
    # 3. Fetch base JSON từ GitHub
    print("📦 Fetching BunchaTV JSON...")
    base_json = json.loads(fetch_text(cfg['sources']['buncha_json']))
    
    # 4. Merge data
    print("🔗 Merging...")
    new_data = merge_data(filtered, cfg, base_json)
    new_json = json.dumps(new_data, ensure_ascii=False, indent=2)
    
    # 5. ✅ LOGIC QUAN TRỌNG: Luôn ghi file lần đầu, sau đó chỉ ghi khi khác
    if OUTPUT_PATH.exists():
        # So sánh hash để tránh ghi không cần thiết
        old_hash = get_file_hash(OUTPUT_PATH)
        new_hash = hashlib.md5(new_json.encode('utf-8')).hexdigest()
        if old_hash == new_hash:
            print("📦 No changes detected. Skipping file update.")
            sys.exit(0)
        else:
            print("🔄 Changes detected. Updating output.json...")
    else:
        # 🎯 Lần đầu chạy: luôn tạo file
        print("✨ First run: Creating output.json...")
    
    # Ghi file
    OUTPUT_PATH.write_text(new_json, encoding='utf-8')
    print(f"✅ Done! Saved to: {OUTPUT_PATH.resolve()}")
    print(f"📊 Total groups: {len(new_data['groups'])} (TV group ở vị trí #1)")
    
    # Exit code 1 để GitHub Actions biết cần commit
    sys.exit(1)

if __name__ == "__main__":
    main()
