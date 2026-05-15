#!/usr/bin/env python3
"""
PC Plus Computing - Branded Image Generator v2
Uses gpt-image-1.5 via Together AI for ChatGPT-quality marketing images.
"""

import os
import sys
import re
import json
import time
import base64
import argparse
import html as htmlmod
import requests
from PIL import Image
from io import BytesIO
from collections import Counter


def strip_emoji(text):
    return re.sub(r'[\U00010000-\U0010ffff☀-➿✀-➿⌀-⏿⭐⭕▪-◿⤴-⤵‼⁉ℹ↔-↙↩-↪⌚-⌛⏩-⏳⏸-⏺Ⓜ▫▶◀◻-◾☑☔-☕☢☣☦☪☮☯☸-☺♈-♓♠♣♥♦♨♻♿⚒-⚗⚙⚛⚜⚠⚡⚪⚫⚰⚱⚽⚾⛄⛅⛈⛎⛏⛑⛓⛔⛩⛪⛰-⛵⛷-⛺⛽✂✅✈-✍✏✒✔✖✝✡✨✳✴❄❇❌❎❓-❕❗❣❤➕-➗➡➰🛠🖥💾🏢☁🔒💻📱🌐🛡🔧📊🏠🖨🔍📡🏪🏥⚖🏘💼📋🔄]', '', text).strip()

OUTPUT_DIR = "output_v2"
FINAL_SIZE = 500
GEN_SIZE = 1024

API_URL = "https://api.together.xyz/v1/images/generations"
MODEL = "openai/gpt-image-1.5"

with open('h3_tags.json') as f:
    _h3data = json.load(f)

_all_h3s = Counter()
for _p, _hs in _h3data.items():
    for _h in _hs:
        _all_h3s[_h] += 1
_shared = {h for h, c in _all_h3s.items() if c >= 10}
_badges = {h for h, c in _all_h3s.items() if c >= 100}
_shared_boxes = _shared - _badges

IMAGES = []
_seen = set()

for page, h3s in sorted(_h3data.items()):
    for h3 in h3s:
        if h3 in _shared:
            continue
        clean = htmlmod.unescape(h3).strip()
        if not clean or clean in _seen:
            continue
        _seen.add(clean)
        safe = clean.lower().replace('&', 'and').replace(' ', '-')
        safe = ''.join(c for c in safe if c.isalnum() or c == '-').strip('-')[:60]
        IMAGES.append({'title': clean, 'filename': safe, 'page': page})

for h3 in sorted(_shared_boxes):
    clean = htmlmod.unescape(h3).strip()
    if clean in _seen:
        continue
    _seen.add(clean)
    safe = clean.lower().replace('&', 'and').replace(' ', '-')
    safe = ''.join(c for c in safe if c.isalnum() or c == '-').strip('-')[:60]
    IMAGES.append({'title': clean, 'filename': safe, 'page': 'shared'})

_surrey_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'surrey-service-cards-master-list.txt')
if os.path.exists(_surrey_file):
    with open(_surrey_file) as _sf:
        _cur_page = 'surrey'
        for _line in _sf:
            _line = _line.strip()
            if _line.startswith('/'):
                _cur_page = _line
            elif _line.startswith('- '):
                clean = _line[2:].strip()
                if not clean or clean in _seen:
                    continue
                _seen.add(clean)
                safe = clean.lower().replace('&', 'and').replace(' ', '-')
                safe = ''.join(c for c in safe if c.isalnum() or c == '-').strip('-')[:60]
                IMAGES.append({'title': clean, 'filename': safe, 'page': _cur_page})


def get_category_context(title):
    t = title.lower()
    if any(w in t for w in ['repair', 'fix', 'replace', 'upgrade', 'diagnostic', 'tune-up', 'overheating', 'boot', 'slow']):
        return "Show a professional technician repairing/working on a computer or device in a modern clean workshop."
    if any(w in t for w in ['security', 'cyber', 'firewall', 'protect', 'malware', 'virus', 'ransomware', 'phishing', 'endpoint', 'edr', 'audit', 'monitor', 'incident']):
        return "Show a cybersecurity theme with digital shield, secure network visualization, or security professional at monitors."
    if any(w in t for w in ['network', 'wi-fi', 'wifi', 'router', 'vpn']):
        return "Show network infrastructure, router, or IT professional setting up networking equipment."
    if any(w in t for w in ['data recovery', 'hard drive', 'ssd', 'raid', 'nas', 'usb', 'deleted', 'format', 'external drive']):
        return "Show data recovery theme with hard drive, precision tools, or clean room environment."
    if any(w in t for w in ['macbook', 'imac', 'mac mini', 'mac virus', 'macos']):
        return "Show Apple MacBook/iMac being serviced by a professional technician in a clean workspace."
    if any(w in t for w in ['laptop']):
        return "Show a professional technician working on a laptop in a modern repair center."
    if any(w in t for w in ['phone', 'tablet', 'iphone', 'android', 'mobile', 'charging']):
        return "Show a technician repairing a smartphone or tablet with precision tools."
    if any(w in t for w in ['website', 'seo', 'design', 'wordpress', 'content', 'page', 'keyword']):
        return "Show a web designer or SEO specialist working on a modern website, dual monitors visible."
    if any(w in t for w in ['cloud', 'backup', 'email', 'microsoft', 'remote work', '365']):
        return "Show cloud computing or office IT setup with professional helping a business client."
    if any(w in t for w in ['server', 'hyper-v', 'proxmox', 'virtualization', 'windows server']):
        return "Show server room with rack servers, blinking lights, IT professional managing infrastructure."
    if any(w in t for w in ['voip', 'sharepoint', 'onedrive', 'patch management', 'compliance', 'siem', 'vlan', 'switch']):
        return "Show IT professional configuring enterprise systems in a modern office with multiple monitors."
    if any(w in t for w in ['emergency', 'urgent', 'downtime', 'priority', 'critical']):
        return "Show IT professional responding urgently to a computer emergency, focused and professional."
    if any(w in t for w in ['business', 'managed', 'helpdesk', 'consulting', 'outsource', 'office', 'server manage', 'maintenance', 'it planning', 'it support', 'device management']):
        return "Show IT professional helping a business client in a modern office environment."
    if any(w in t for w in ['surrey', 'vancouver', 'burnaby', 'langley', 'richmond', 'coquitlam', 'delta', 'white rock']):
        return f"Show a professional IT service van or storefront in {title}, BC with the city visible."
    if any(w in t for w in ['realtor', 'accountant', 'law', 'immigration', 'medical', 'restaurant', 'retail', 'small office']):
        return f"Show a professional {title.lower()} office with modern IT setup, computers and technology visible."
    if any(w in t for w in ['printer']):
        return "Show IT professional helping with printer setup or troubleshooting in an office."
    if any(w in t for w in ['proactive', 'prevention', 'helpful', 'experienced']):
        return "Show friendly IT professional team ready to help, modern office background."
    return "Show a professional IT service scene with modern technology, clean workspace."


def get_bullets(title):
    t = title.lower()
    if 'computer repair' in t: return ["Diagnostics & Repair", "Hardware & Software", "Virus Removal", "Performance Tune-Up"]
    if 'laptop repair' in t: return ["Screen Repair", "Battery Replacement", "Keyboard Fix", "Software Solutions"]
    if 'macbook' in t or 'mac' in t: return ["Apple Certified", "Screen & Battery", "Data Recovery", "OS Repair"]
    if 'data recovery' in t or 'drive' in t or 'deleted' in t or 'ssd data' in t: return ["Hard Drive Recovery", "SSD Recovery", "Deleted Files", "RAID Recovery"]
    if 'security' in t or 'cyber' in t or 'firewall' in t or 'virus' in t or 'malware' in t or 'ransomware' in t or 'phishing' in t: return ["Threat Detection", "Real-Time Protection", "Security Audits", "24/7 Monitoring"]
    if 'network' in t or 'wi-fi' in t or 'wifi' in t or 'router' in t or 'vpn' in t or 'cabling' in t or 'vlan' in t or 'switch' in t: return ["Network Setup", "Wi-Fi Optimization", "Troubleshooting", "Secure Connections"]
    if 'server' in t or 'hyper-v' in t or 'proxmox' in t or 'virtualization' in t: return ["Server Setup", "Monitoring", "Maintenance", "Security"]
    if 'emergency' in t or 'urgent' in t or 'critical' in t or 'downtime' in t: return ["Fast Response", "Priority Service", "Expert Diagnosis", "Business Recovery"]
    if 'endpoint' in t or 'patch' in t or 'compliance' in t or 'siem' in t or 'monitoring' in t: return ["24/7 Monitoring", "Threat Detection", "Compliance Ready", "Proactive Support"]
    if 'business' in t or 'managed' in t or 'helpdesk' in t or 'consulting' in t or 'office' in t: return ["Managed IT Services", "IT Support", "Cloud Solutions", "IT Consulting"]
    if 'phone' in t or 'tablet' in t or 'iphone' in t or 'android' in t: return ["Screen Repair", "Battery Replace", "Charging Port Fix", "Data Recovery"]
    if 'website' in t or 'seo' in t or 'design' in t or 'wordpress' in t: return ["Custom Design", "SEO Friendly", "Mobile Responsive", "Fast & Secure"]
    if 'cloud' in t or 'backup' in t or 'email' in t or 'microsoft' in t or '365' in t: return ["Cloud Migration", "Email Setup", "Data Backup", "24/7 Support"]
    if 'printer' in t: return ["Setup & Config", "Troubleshooting", "Network Printing", "Driver Support"]
    return ["Expert Service", "Fast Turnaround", "Trusted Support", "Satisfaction Guaranteed"]


LOGO_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logo.png")


def build_prompt(title, bullets):
    scene = get_category_context(title)
    bullet_str = ", ".join(bullets)
    return f"""Create a 500x500 branded service image for PC Plus Computing, a professional IT company in Vancouver BC.

Style: Light themed with bright white and light blue color palette. Professional, clean, modern marketing design.
{scene}
IMPORTANT: Leave the top-left corner area (roughly 220x70 pixels) empty/clean with a light background - a real logo will be placed there later.
Main title in large bold text: {title}
Include 4 service bullet points with blue checkmark icons: {bullet_str}
Blue footer bar at bottom with: pcpluscomputing.com | 604-760-1662
Professional computer repair / IT support marketing card style.
Clean readable text. High quality commercial design look. No extra paragraphs or unnecessary text."""


def composite_logo(img):
    if not os.path.exists(LOGO_PATH):
        return img
    logo = Image.open(LOGO_PATH).convert('RGBA')
    logo_w = 200
    logo_h = int(logo.height * (logo_w / logo.width))
    logo = logo.resize((logo_w, logo_h), Image.LANCZOS)
    img = img.convert('RGBA')
    white_bg = Image.new('RGBA', (logo_w + 10, logo_h + 10), (255, 255, 255, 230))
    img.paste(white_bg, (5, 5), white_bg)
    img.paste(logo, (10, 8), logo)
    return img.convert('RGB')


def generate_image(title, output_path, api_key, retries=2):
    title = strip_emoji(title)
    bullets = get_bullets(title)
    prompt = build_prompt(title, bullets)

    for attempt in range(retries + 1):
        resp = requests.post(API_URL,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={"model": MODEL, "prompt": prompt, "width": GEN_SIZE, "height": GEN_SIZE, "n": 1, "response_format": "b64_json"},
            timeout=120)
        if resp.status_code == 400 and attempt < retries:
            time.sleep(3)
            continue
        resp.raise_for_status()
        break

    b64 = resp.json()["data"][0]["b64_json"]
    img = Image.open(BytesIO(base64.b64decode(b64)))
    img = img.resize((FINAL_SIZE, FINAL_SIZE), Image.LANCZOS)
    img = composite_logo(img)

    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else '.', exist_ok=True)
    img.save(output_path, "PNG", optimize=True)
    return os.path.getsize(output_path)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--start-from", type=int, default=1)
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    api_key = os.environ.get("TOGETHER_API_KEY")
    if not api_key and not args.dry_run:
        print("Set TOGETHER_API_KEY"); sys.exit(1)

    print(f"PC Plus - Branded Image Generator v2 (gpt-image-1.5)")
    print(f"Total images: {len(IMAGES)}")
    print()

    if args.dry_run:
        for i, img in enumerate(IMAGES, 1):
            bullets = get_bullets(img['title'])
            print(f"[{i}] {img['title']} -> {img['filename']}.png")
            print(f"    Bullets: {', '.join(bullets)}")
        return

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    total = len(IMAGES)
    success = 0
    failed = 0
    failed_list = []

    for i, img in enumerate(IMAGES, 1):
        if i < args.start_from:
            continue
        if args.limit > 0 and i >= args.start_from + args.limit:
            break

        output_path = os.path.join(OUTPUT_DIR, f"{img['filename']}.png")
        if os.path.exists(output_path) and os.path.getsize(output_path) > 10000:
            print(f"  [{i}/{total}] SKIP: {img['title']}")
            continue

        print(f"  [{i}/{total}] {img['title']}")
        try:
            size = generate_image(img['title'], output_path, api_key)
            print(f"    -> {output_path} ({size//1024}KB)")
            success += 1
            time.sleep(1)
        except requests.exceptions.HTTPError as e:
            print(f"    FAILED: {e}")
            failed += 1
            failed_list.append(img['title'])
            if "429" in str(e):
                print("    Rate limited, waiting 45s...")
                time.sleep(45)
            elif "402" in str(e):
                print("    Out of credits! Add more at together.ai")
                break
        except Exception as e:
            print(f"    FAILED: {e}")
            failed += 1
            failed_list.append(img['title'])

    print(f"\nDone! Success: {success}, Failed: {failed}")
    if failed_list:
        print("Failed images:")
        for f in failed_list:
            print(f"  - {f}")

if __name__ == "__main__":
    main()
