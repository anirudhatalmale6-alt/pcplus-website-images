#!/usr/bin/env python3
"""
PC Plus Computing - Final Image Generator (Hybrid Approach)
Generates branded 500x500 service card images.

HYBRID: AI generates background scene + Pillow overlays branding/text
Result: Professional backgrounds + pixel-perfect text every time.

Supports 3 backends (cheapest to most expensive):
  --backend together   (FLUX Schnell - FREE for 3 months)
  --backend replicate  (FLUX Schnell - $0.003/image, ~$0.50 total)
  --backend openai     (gpt-image-1 - $0.04/image, ~$6.50 total)

Usage:
  export TOGETHER_API_KEY=xxx   # or REPLICATE_API_TOKEN or OPENAI_API_KEY
  python generate_final.py --backend together
  python generate_final.py --backend replicate
  python generate_final.py --backend openai
  python generate_final.py --start-from 50   # resume
  python generate_final.py --dry-run          # preview only
"""

import os
import sys
import json
import time
import base64
import argparse
import urllib.request
import urllib.error
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

OUTPUT_DIR = "output"
BG_DIR = "backgrounds"
FINAL_SIZE = 500
BG_SIZE = 1024

FONT_BOLD = "/usr/share/fonts/truetype/lato/Lato-Bold.ttf"
FONT_SEMI = "/usr/share/fonts/truetype/lato/Lato-Semibold.ttf"
FONT_REG = "/usr/share/fonts/truetype/lato/Lato-Medium.ttf"

WHITE = (255, 255, 255)
DARK_BLUE = (10, 35, 80)
BRAND_BLUE = (0, 120, 200)
LIGHT_BG = (240, 248, 255)
FOOTER_BLUE = (0, 100, 180)

with open('h3_tags.json') as f:
    _h3data = json.load(f)

from collections import Counter
_all_h3s = Counter()
for _p, _hs in _h3data.items():
    for _h in _hs:
        _all_h3s[_h] += 1
_shared = {h for h, c in _all_h3s.items() if c >= 10}

IMAGES = []
_seen = set()
for page, h3s in sorted(_h3data.items()):
    for h3 in h3s:
        if h3 in _shared:
            continue
        import html as htmlmod
        clean = htmlmod.unescape(h3).strip()
        if not clean or clean in _seen:
            continue
        _seen.add(clean)
        safe = clean.lower().replace('&', 'and').replace(' ', '-')
        safe = ''.join(c for c in safe if c.isalnum() or c == '-')
        safe = safe.strip('-')[:60]
        IMAGES.append({
            'title': clean,
            'filename': safe,
            'page': page,
        })

for h3 in sorted(_shared - {h for h, c in _all_h3s.items() if c >= 100}):
    clean = htmlmod.unescape(h3).strip()
    safe = clean.lower().replace('&', 'and').replace(' ', '-')
    safe = ''.join(c for c in safe if c.isalnum() or c == '-')
    safe = safe.strip('-')[:60]
    IMAGES.append({
        'title': clean,
        'filename': safe,
        'page': 'shared',
    })

def get_bg_prompt(title):
    t = title.lower()
    if any(w in t for w in ['repair', 'fix', 'replace', 'upgrade', 'diagnostic']):
        return f"Professional IT technician working on {title.lower()}, clean modern computer repair workshop, bright lighting, blue and white color scheme, no text"
    if any(w in t for w in ['security', 'cyber', 'firewall', 'protect', 'malware', 'virus', 'ransomware', 'phishing', 'endpoint', 'edr', 'audit', 'monitor']):
        return f"Modern cybersecurity operations center, digital shield hologram, blue glowing network visualization, dark background with blue accents, no text"
    if any(w in t for w in ['network', 'wi-fi', 'wifi', 'router', 'vpn']):
        return f"Modern network server room with ethernet cables and blinking lights, professional IT infrastructure, blue LED lighting, no text"
    if any(w in t for w in ['data recovery', 'hard drive', 'ssd', 'raid', 'nas', 'usb', 'deleted', 'format', 'external drive']):
        return f"Professional data recovery lab, hard drive being examined, clean room environment, blue lighting, precision tools, no text"
    if any(w in t for w in ['business', 'managed', 'helpdesk', 'consulting', 'outsource', 'office', 'server manage', 'maintenance']):
        return f"Modern business office with IT professional helping client, clean workspace, monitors and laptops, professional atmosphere, blue accents, no text"
    if any(w in t for w in ['macbook', 'imac', 'mac mini', 'mac virus', 'macos']):
        return f"Apple MacBook being repaired by technician, clean white workspace, precision tools, bright professional environment, no text"
    if any(w in t for w in ['laptop']):
        return f"Professional laptop repair technician working on open laptop, modern repair bench, bright lighting, tools visible, no text"
    if any(w in t for w in ['phone', 'tablet', 'iphone', 'android', 'mobile', 'charging port']):
        return f"Mobile phone repair technician working on smartphone, precision tools, magnifying lamp, clean bench, professional, no text"
    if any(w in t for w in ['website', 'seo', 'design', 'wordpress', 'content', 'page']):
        return f"Web designer working on modern website, dual monitors showing responsive design, creative workspace, blue accents, no text"
    if any(w in t for w in ['cloud', 'backup', 'email', 'microsoft', 'remote work', '365']):
        return f"Cloud computing visualization, modern office with cloud icons, server racks, blue holographic displays, professional, no text"
    if any(w in t for w in ['surrey', 'vancouver', 'burnaby', 'langley', 'richmond', 'coquitlam', 'delta', 'white rock']):
        return f"Beautiful cityscape of {title}, British Columbia, Canada, professional photography, blue sky, modern buildings, no text"
    if any(w in t for w in ['realtor', 'accountant', 'law', 'immigration', 'medical', 'restaurant', 'retail', 'small office']):
        return f"Professional {title.lower()} office with modern technology setup, computer on desk, clean workspace, blue accents, no text"
    return f"Professional IT service for {title.lower()}, modern technology workspace, blue and white color scheme, clean bright environment, no text"


def generate_bg_together(title, output_path, api_key):
    prompt = get_bg_prompt(title)
    payload = json.dumps({
        "model": "black-forest-labs/FLUX.1-schnell",
        "prompt": prompt,
        "width": BG_SIZE,
        "height": BG_SIZE,
        "steps": 4,
        "n": 1,
        "response_format": "b64_json"
    }).encode()
    req = urllib.request.Request(
        "https://api.together.xyz/v1/images/generations",
        data=payload,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        result = json.loads(resp.read().decode())
    b64 = result["data"][0]["b64_json"]
    img = Image.open(BytesIO(base64.b64decode(b64)))
    img.save(output_path, "PNG")
    return img

def generate_bg_replicate(title, output_path, api_key):
    prompt = get_bg_prompt(title)
    payload = json.dumps({
        "input": {
            "prompt": prompt,
            "go_fast": True,
            "num_outputs": 1,
            "aspect_ratio": "1:1",
            "output_format": "png",
            "output_quality": 90
        }
    }).encode()
    req = urllib.request.Request(
        "https://api.replicate.com/v1/models/black-forest-labs/flux-schnell/predictions",
        data=payload,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json", "Prefer": "wait"}
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        result = json.loads(resp.read().decode())
    img_url = result["output"][0]
    img_req = urllib.request.Request(img_url)
    with urllib.request.urlopen(img_req, timeout=60) as img_resp:
        img = Image.open(BytesIO(img_resp.read()))
    img.save(output_path, "PNG")
    return img

def generate_bg_openai(title, output_path, api_key):
    prompt = get_bg_prompt(title)
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        result = client.images.generate(
            model="gpt-image-1",
            prompt=prompt,
            size="1024x1024",
            quality="medium",
        )
        b64 = result.data[0].b64_json
        img = Image.open(BytesIO(base64.b64decode(b64)))
    except ImportError:
        payload = json.dumps({
            "model": "dall-e-3",
            "prompt": prompt,
            "n": 1,
            "size": "1024x1024",
            "quality": "standard",
            "response_format": "url"
        }).encode()
        req = urllib.request.Request(
            "https://api.openai.com/v1/images/generations",
            data=payload,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=120) as resp:
            result = json.loads(resp.read().decode())
        img_url = result["data"][0]["url"]
        with urllib.request.urlopen(img_url, timeout=60) as img_resp:
            img = Image.open(BytesIO(img_resp.read()))
    img.save(output_path, "PNG")
    return img


def wrap_text(text, font, max_width, draw):
    if "\n" in text:
        result = []
        for line in text.split("\n"):
            result.extend(wrap_text(line, font, max_width, draw))
        return result
    words = text.split()
    lines, current = [], ""
    for word in words:
        test = f"{current} {word}".strip()
        bbox = draw.textbbox((0, 0), test, font=font)
        if bbox[2] - bbox[0] > max_width and current:
            lines.append(current)
            current = word
        else:
            current = test
    if current:
        lines.append(current)
    return lines

def overlay_branding(bg_img, title):
    bg = bg_img.resize((FINAL_SIZE, FINAL_SIZE), Image.LANCZOS)
    darken = ImageEnhance.Brightness(bg).enhance(0.45)
    blue_overlay = Image.new('RGBA', (FINAL_SIZE, FINAL_SIZE), (5, 25, 65, 140))
    canvas = Image.new('RGBA', (FINAL_SIZE, FINAL_SIZE))
    canvas.paste(darken.convert('RGBA'))
    canvas = Image.alpha_composite(canvas, blue_overlay)
    draw = ImageDraw.Draw(canvas)

    # Title
    for size in range(56, 22, -2):
        font = ImageFont.truetype(FONT_BOLD, size)
        lines = wrap_text(title, font, FINAL_SIZE - 60, draw)
        total_h = len(lines) * (size + 8)
        if total_h < FINAL_SIZE - 120:
            break

    line_h = size + 8
    total_h = len(lines) * line_h
    y = (FINAL_SIZE - total_h) // 2 - 20

    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        lw = bbox[2] - bbox[0]
        x = (FINAL_SIZE - lw) // 2
        draw.text((x + 2, y + 2), line, font=font, fill=(0, 0, 0, 150))
        draw.text((x, y), line, font=font, fill=WHITE)
        y += line_h

    # Footer bar
    footer_y = FINAL_SIZE - 42
    draw.rectangle([0, footer_y, FINAL_SIZE, FINAL_SIZE], fill=(0, 80, 160, 220))
    footer_font = ImageFont.truetype(FONT_REG, 13)
    footer_text = "pcpluscomputing.com    604-760-1662"
    bbox = draw.textbbox((0, 0), footer_text, font=footer_font)
    fw = bbox[2] - bbox[0]
    draw.text(((FINAL_SIZE - fw) // 2, footer_y + 12), footer_text, font=footer_font, fill=WHITE)

    # Top accent line
    draw.rectangle([0, 0, FINAL_SIZE, 4], fill=(0, 150, 220, 200))

    return canvas.convert('RGB')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--backend", choices=["together", "replicate", "openai"], default="together")
    parser.add_argument("--start-from", type=int, default=1)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--limit", type=int, default=0, help="Generate only N images (for testing)")
    args = parser.parse_args()

    env_keys = {
        "together": "TOGETHER_API_KEY",
        "replicate": "REPLICATE_API_TOKEN",
        "openai": "OPENAI_API_KEY",
    }
    api_key = os.environ.get(env_keys[args.backend])

    print(f"PC Plus Computing - Branded Image Generator")
    print(f"Backend: {args.backend}")
    print(f"Total images: {len(IMAGES)}")
    print(f"Output: {FINAL_SIZE}x{FINAL_SIZE} PNG with branding overlay")
    print()

    if args.dry_run:
        for i, img in enumerate(IMAGES, 1):
            prompt = get_bg_prompt(img['title'])
            print(f"[{i}] {img['title']}")
            print(f"    File: {img['filename']}.png")
            print(f"    Prompt: {prompt[:100]}...")
            print()
        return

    if not api_key:
        print(f"Set {env_keys[args.backend]} environment variable:")
        print(f"  export {env_keys[args.backend]}=your_key_here")
        sys.exit(1)

    generators = {
        "together": generate_bg_together,
        "replicate": generate_bg_replicate,
        "openai": generate_bg_openai,
    }
    gen_fn = generators[args.backend]

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(BG_DIR, exist_ok=True)

    total = len(IMAGES)
    if args.limit > 0:
        total = min(total, args.start_from - 1 + args.limit)

    success = 0
    failed = 0

    for i, img in enumerate(IMAGES, 1):
        if i < args.start_from:
            continue
        if args.limit > 0 and i >= args.start_from + args.limit:
            break

        title = img['title']
        fname = img['filename']
        output_path = os.path.join(OUTPUT_DIR, f"{fname}.png")
        bg_path = os.path.join(BG_DIR, f"{fname}_bg.png")

        if os.path.exists(output_path) and os.path.getsize(output_path) > 5000:
            print(f"  [{i}/{total}] SKIP: {title}")
            continue

        print(f"  [{i}/{total}] {title}")
        try:
            if os.path.exists(bg_path) and os.path.getsize(bg_path) > 5000:
                bg = Image.open(bg_path)
            else:
                bg = gen_fn(title, bg_path, api_key)

            final = overlay_branding(bg, title)
            final.save(output_path, "PNG", optimize=True)
            size_kb = os.path.getsize(output_path) // 1024
            print(f"    -> {output_path} ({size_kb}KB)")
            success += 1
            time.sleep(0.5)

        except Exception as e:
            print(f"    FAILED: {e}")
            failed += 1
            if "429" in str(e) or "rate" in str(e).lower():
                print("    Rate limited, waiting 30s...")
                time.sleep(30)

    print(f"\nDone! Success: {success}, Failed: {failed}")

if __name__ == "__main__":
    main()
