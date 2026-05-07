#!/usr/bin/env python3
# scraper.py - Parse M3U + Merge BunchaTV + Force update support

import json
import re
import yaml
import sys
import hashlib
import argparse
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
        '
