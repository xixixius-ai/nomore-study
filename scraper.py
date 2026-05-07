#!/usr/bin/env python3
# scraper.py - Auto-detect JSON/M3U + Merge với buncha

import json
import re
import requests
from pathlib import Path

HAILAB_URL = "https://tv.hailab.cloud/"
BUNCHA_URL = "https://raw.githubusercontent.com/xixixius-ai/buncha-stream/refs/heads/main/output.json"

def fetch_content(url):
    """Fetch với headers đầy đủ để tránh bị chặn"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': '*/*',
        'Accept-Language': 'en-US,en;q=0.9',
    }
    resp = requests.get(url, headers=headers, timeout=30)
    resp.raise_for_status()
    return resp.text.strip(), resp.headers.get('Content-Type', '')

def parse_json_or_m3u(content, content_type):
    """Tự động parse JSON hoặc M3U"""
    
    # ✅ Trường hợp 1: JSON trực tiếp
    if content_type.startswith('application/json') or content.startswith('{'):
        try:
            data = json.loads(content)
            print("✅ Detected: JSON format")
            return extract_tv_channels_from_json(data)
        except json.JSONDecodeError:
            pass
    
    # ✅ Trường hợp 2: M3U playlist
    if content.startswith('#EXTM3U') or '#EXTINF:' in content:
        print("✅ Detected: M3U format")
        return parse_m3u_channels(content)
    
    # ❌ Không nhận diện được
    print(f"❌ Unknown format. Content-Type: {content_type}")
    print(f"🔤 Preview: {content[:200]}")
    return []

def extract_tv_channels_from_json(data):
    """Lọc kênh từ JSON format (như tv.hailab.cloud)"""
    channels = []
    for group in data.get('groups', []):
        if group.get('name') == 'Kênh VTV':
            channels.extend(group.get('channels', []))
        for ch in group.get('channels', []):
            if ch.get('name') == 'HTV Thể Thao' and ch not in channels:
                channels.append(ch)
    return channels

def parse_m3u_channels(content):
    """Parse M3U → list channels"""
    channels = []
    lines = [l.strip() for l in content.split('\n') if l.strip()]
    current = None
    
    for line in lines:
        if line.startswith('#EXTINF:'):
            name = re.search(r',(.+)$', line)
            name = name.group(1).strip() if name else ''
            logo = re.search(r'tvg-logo="([^"]*)"', line)
            logo = logo.group(1) if logo else ''
            group = re.search(r'group-title="([^"]*)"', line)
            group = group.group(1) if group else ''
            url_match = None  # Sẽ lấy ở dòng sau
            current = {'name': name, 'logo': logo, 'group': group}
        elif line.startswith('http') and current:
            if current['group'] == 'Kênh VTV' or current['name'] == 'HTV Thể Thao':
                channels.append({
                    'id': f"tv-{len(channels)}",
                    'name': current['name'],
                    'url': line,
                    'logo': current['logo']
                })
            current = None
    return channels

def main():
    print("🚀 Starting scraper...")
    
    # 1. Fetch hailab
    print(f"📡 Fetching {HAILAB_URL}...")
    try:
        content, content_type = fetch_content(HAILAB_URL)
        tv_channels = parse_json_or_m3u(content, content_type)
        print(f"✅ Lấy được {len(tv_channels)} kênh TV")
    except Exception as e:
        print(f"❌ Error fetching hailab: {e}")
        tv_channels = []
    
    # 2. Fetch buncha
    print("📦 Fetching buncha JSON...")
    try:
        buncha = requests.get(BUNCHA_URL, timeout=30).json()
    except Exception as e:
        print(f"❌ Error fetching buncha: {e}")
        return
    
    # 3. Merge
    tv_group = {
        "id": "grp-tv-channels",
        "name": "📺 Kênh Truyền Hình",
        "display": "vertical",
        "grid_number": 3,
        "enable_detail": False,
        "channels": tv_channels
    }
    
    result = {**buncha, "groups": [tv_group] + buncha.get('groups', [])}
    
    # 4. Save
    output = Path("output.json")
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    
    print(f"✨ DONE! Saved to: {output.resolve()}")
    print(f"📊 Total groups: {len(result['groups'])}")

if __name__ == "__main__":
    main()
