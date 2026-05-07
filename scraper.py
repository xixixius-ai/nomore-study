#!/usr/bin/env python3
# scraper.py - Fetch M3U local + Merge với BunchaTV JSON
# Cách dùng: python scraper.py

import json
import re
import yaml
from pathlib import Path
import requests

def load_config(path: str = "config.yml") -> dict:
    """Load cấu hình từ YAML"""
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def fetch_text(url_or_path: str) -> str:
    """Fetch content: hỗ trợ cả file local và URL"""
    path = Path(url_or_path)
    # Nếu là file local tồn tại → đọc file
    if path.exists() and path.is_file():
        return path.read_text(encoding='utf-8')
    # Ngược lại → fetch URL
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': '*/*',
    }
    resp = requests.get(url_or_path, headers=headers, timeout=30)
    resp.raise_for_status()
    return resp.text

def parse_m3u_channels(m3u_content: str) -> list:
    """Parse M3U content → list channels"""
    lines = [l.strip() for l in m3u_content.split('\n') if l.strip()]
    channels, current_meta = [], None
    
    for line in lines:
        if line.startswith('#EXTINF:'):
            name_match = re.search(r',(.+)$', line)
            name = name_match.group(1).strip() if name_match else ''
            attrs = dict(re.findall(r'(\w+(?:-\w+)*)="([^"]*)"', line))
            current_meta = {'name': name, **attrs}
        elif line.startswith('http') and current_meta:
            channels.append({
                'name': current_meta.get('name', ''),
                'url': line,
                'logo': current_meta.get('tvg-logo', ''),
                'group': current_meta.get('group-title', 'Uncategorized'),
                'tvg_id': current_meta.get('tvg-id', '')
            })
            current_meta = None
    return channels

def filter_channels(channels: list, filters: dict) -> list:
    """Lọc kênh theo allowed_groups và allowed_names"""
    allowed_groups = filters.get('allowed_groups', [])
    allowed_names = filters.get('allowed_names', [])
    result = []
    
    for ch in channels:
        # Ưu tiên lọc theo tên chính xác
        if allowed_names and ch['name'] in allowed_names:
            result.append(ch)
        # Hoặc lọc theo group-title
        elif allowed_groups and ch['group'] in allowed_groups:
            result.append(ch)
    return result

def create_channel_entry(ch: dict, idx: int, cfg: dict) -> dict:
    """Tạo channel object minimal - app đọc được ngay"""
    defaults = cfg.get('channel_defaults', {})
    entry = {
        'id': f"tv-{ch['tvg_id'] or idx}" if ch['tvg_id'] else f"tv-{idx}",
        'name': ch['name'],
        'url': ch['url'],          # ✅ Link M3U gốc, app đọc trực tiếp
        'logo': ch['logo'],        # ✅ Logo từ tvg-logo
        'group': ch['group'],
    }
    
    # Thêm metadata nếu app cần
    for key in ['type', 'display', 'enable_detail']:
        if key in defaults:
            entry[key] = defaults[key]
    
    # Thêm label LIVE
    if defaults.get('add_live_label'):
        entry['labels'] = [{
            'text': '● LIVE',
            'position': 'top-left',
            'color': '#00000080',
            'text_color': '#ff4444'
        }]
    
    # Thêm headers để tránh 403
    if defaults.get('add_referer_header') and defaults.get('referer_url'):
        entry['request_headers'] = [
            {'key': 'Referer', 'value': defaults['referer_url']},
            {'key': 'User-Agent', 'value': 'Mozilla/5.0'}
        ]
    
    return entry

def create_tv_group(channels: list, group_cfg: dict, main_cfg: dict) -> dict:
    """Tạo group TV với các channel đã lọc"""
    return {
        'id': group_cfg['id'],
        'name': group_cfg['name'],      # 📺 Kênh Truyền Hình
        'display': group_cfg.get('display', 'vertical'),
        'grid_number': group_cfg.get('grid_number', 3),
        'enable_detail': group_cfg.get('enable_detail', False),
        'channels': [
            create_channel_entry(ch, idx, main_cfg)
            for idx, ch in enumerate(channels)
        ]
    }

def merge_data(tv_group: dict, buncha_json: dict) -> dict:
    """Merge: TV group ở vị trí ĐẦU tiên"""
    return {
        **buncha_json,
        'groups': [tv_group] + buncha_json.get('groups', [])  # ⭐ TV group lên đầu
    }

def main():
    print("🚀 Starting scraper...")
    cfg = load_config()
    
    # 1. Đọc file M3U local
    m3u_path = cfg['sources']['m3u_file']
    print(f"📂 Reading {m3u_path}...")
    m3u_content = fetch_text(m3u_path)
    
    # 2. Parse & filter channels
    print("🔍 Filtering channels...")
    all_channels = parse_m3u_channels(m3u_content)
    filtered = filter_channels(all_channels, cfg['filters'])
    print(f"✅ Selected {len(filtered)}/{len(all_channels)} channels:")
    for ch in filtered:
        print(f"   • {ch['name']} [{ch['group']}]")
    
    # 3. Fetch base JSON từ GitHub
    print("📦 Fetching BunchaTV JSON...")
    buncha_data = json.loads(fetch_text(cfg['sources']['buncha_json']))
    
    # 4. Create TV group & merge
    print("🔗 Merging...")
    tv_group = create_tv_group(filtered, cfg['tv_group'], cfg)
    result = merge_data(tv_group, buncha_data)
    
    # 5. Save output
    output_path = Path('output.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"✨ Done! Saved to: {output_path.resolve()}")
    print(f"📊 Total groups: {len(result['groups'])} (TV group ở vị trí #1 🎯)")

if __name__ == "__main__":
    main()
