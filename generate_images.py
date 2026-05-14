#!/usr/bin/env python3
"""
PC Plus Computing - Website Image Generator
Generates professional images for all 128 service pages using OpenAI DALL-E 3.
Creates folder structure matching URL paths. Each folder gets a hero image + supporting images.

Usage:
  python generate_images.py --api-key YOUR_OPENAI_API_KEY
  python generate_images.py --api-key YOUR_OPENAI_API_KEY --start-from 50
  python generate_images.py --prompts-only  (just create folders + prompts.csv, no generation)
"""

import os
import sys
import json
import csv
import time
import argparse
import re
import urllib.request
import urllib.error

OUTPUT_DIR = "images"

PAGES = [
    ("homepage", "PC Plus Computing homepage - full-service IT company in Vancouver BC"),
    ("about", "About PC Plus Computing - IT professionals team in Vancouver"),
    ("appointments", "Book an appointment for computer repair or IT support"),
    ("contact-us", "Contact PC Plus Computing for IT services"),
    ("services/backup-disaster-recovery", "Backup and disaster recovery solutions for businesses"),
    ("services/business-it-services", "Business IT services and managed IT support"),
    ("services/cloud-migration", "Cloud migration services - moving business to the cloud"),
    ("services/computer-networking", "Computer networking setup and configuration"),
    ("services/computer-repair", "Computer repair services - desktop and PC repair"),
    ("services/computer-repair/computer-diagnostics", "Computer diagnostics and troubleshooting"),
    ("services/computer-repair/custom-pc-build", "Custom PC building service"),
    ("services/computer-repair/desktop-repair", "Desktop computer repair"),
    ("services/computer-repair/gaming-computer-repair", "Gaming computer repair and optimization"),
    ("services/computer-repair/hardware-repair", "Computer hardware repair and replacement"),
    ("services/computer-repair/linux-repair", "Linux computer repair and support"),
    ("services/computer-repair/motherboard-repair", "Motherboard repair and replacement"),
    ("services/computer-repair/password-recovery", "Computer password recovery service"),
    ("services/computer-repair/pc-upgrade", "PC upgrade service - RAM, SSD, GPU upgrades"),
    ("services/computer-repair/server-repair", "Server repair and maintenance"),
    ("services/computer-repair/slow-computer-fix", "Slow computer fix and optimization"),
    ("services/computer-repair/software-repair", "Software troubleshooting and repair"),
    ("services/computer-repair/windows-repair", "Windows OS repair and reinstallation"),
    ("services/cyber-security-services", "Cybersecurity services for businesses"),
    ("services/data-recovery", "Data recovery from damaged drives and devices"),
    ("services/imac-repair", "iMac repair services"),
    ("services/it-support", "IT support services for home and business"),
    ("services/laptop-repair", "Laptop repair services"),
    ("services/mac-mini-repair", "Mac Mini repair and upgrade services"),
    ("services/macbook-repair", "MacBook repair services"),
    ("services/managed-it-services", "Managed IT services for businesses"),
    ("services/network-setup", "Network setup and installation"),
    ("services/on-site-computer-support", "On-site computer support - we come to you"),
    ("services/onsite-computer-support", "Onsite computer support services"),
    ("services/phone-tablet-repair", "Phone and tablet repair services"),
    ("services/remote-support", "Remote computer support services"),
    ("services/seo-services", "SEO services for small businesses"),
    ("services/virus-removal", "Virus and malware removal services"),
    ("services/website-design", "Website design and development services"),
    ("services/computer-repair/power-supply-repair", "Power supply repair and replacement"),
    ("services/laptop-repair/laptop-screen-repair", "Laptop screen repair and replacement"),
    ("services/laptop-repair/laptop-battery-replacement", "Laptop battery replacement service"),
    ("services/computer-repair/overheating-fix", "Computer overheating fix - thermal paste and cooling"),
    ("services/laptop-repair/laptop-charging-port-repair", "Laptop charging port repair"),
    ("services/computer-repair/boot-error-repair", "Boot error and startup issue repair"),
    ("services/laptop-repair/laptop-water-damage-repair", "Laptop water damage repair"),
    ("services/laptop-repair/laptop-keyboard-repair", "Laptop keyboard repair and replacement"),
    ("services/laptop-repair/gaming-laptop-repair", "Gaming laptop repair"),
    ("services/computer-repair/system-optimization", "System optimization and performance tuning"),
    ("services/laptop-repair/gaming-laptop-upgrade", "Gaming laptop upgrade service"),
    ("services/data-recovery/phone-data-recovery", "Phone data recovery service"),
    ("services/laptop-repair/laptop-boot-issue", "Laptop boot issue troubleshooting"),
    ("services/macbook-repair/macbook-screen-repair", "MacBook screen repair"),
    ("services/macbook-repair/macbook-ssd-upgrade", "MacBook SSD upgrade"),
    ("services/data-recovery/server-data-recovery", "Server data recovery"),
    ("services/macbook-repair/macbook-os-repair", "MacBook OS repair and reinstallation"),
    ("services/macbook-repair/macbook-battery-replacement", "MacBook battery replacement"),
    ("services/macbook-repair/macbook-keyboard-repair", "MacBook keyboard repair"),
    ("services/data-recovery/raid-data-recovery", "RAID data recovery service"),
    ("services/macbook-repair/macbook-data-recovery", "MacBook data recovery"),
    ("services/imac-repair/imac-screen-repair", "iMac screen repair"),
    ("services/macbook-repair/macbook-pro-repair", "MacBook Pro repair"),
    ("services/data-recovery/nas-data-recovery", "NAS data recovery service"),
    ("services/imac-repair/imac-hard-drive-replacement", "iMac hard drive replacement"),
    ("services/laptop-repair/laptop-overheating-fix", "Laptop overheating fix"),
    ("services/laptop-repair/laptop-slow-performance", "Laptop slow performance fix"),
    ("services/laptop-repair/laptop-motherboard-repair", "Laptop motherboard repair"),
    ("services/laptop-repair/laptop-hinge-repair", "Laptop hinge repair"),
    ("services/laptop-repair/laptop-fan-repair", "Laptop fan repair and replacement"),
    ("services/laptop-repair/laptop-diagnostics", "Laptop diagnostics service"),
    ("services/laptop-repair/laptop-software-repair", "Laptop software repair"),
    ("services/laptop-repair/laptop-hard-drive-replacement", "Laptop hard drive replacement"),
    ("services/laptop-repair/laptop-ssd-upgrade", "Laptop SSD upgrade"),
    ("services/mac-mini-repair/mac-mini-upgrade", "Mac Mini upgrade - RAM and storage"),
    ("services/macbook-repair/macbook-overheating", "MacBook overheating fix"),
    ("services/mac-mini-repair/mac-mini-diagnostics", "Mac Mini diagnostics"),
    ("services/macbook-repair/macbook-slow-performance", "MacBook slow performance fix"),
    ("services/macbook-repair/macbook-diagnostics", "MacBook diagnostics"),
    ("services/data-recovery/hard-drive-data-recovery", "Hard drive data recovery"),
    ("deleted-file-recovery", "Deleted file recovery service"),
    ("services/data-recovery/ssd-data-recovery", "SSD data recovery"),
    ("services/data-recovery/usb-data-recovery", "USB drive data recovery"),
    ("services/data-recovery/formatted-drive-recovery", "Formatted drive data recovery"),
    ("services/data-recovery/water-damaged-drive", "Water damaged drive data recovery"),
    ("services/data-recovery/emergency-data-recovery", "Emergency data recovery - 24/7"),
    ("services/data-recovery/external-drive-recovery", "External drive data recovery"),
    ("services/cyber-security-services/endpoint-protection", "Endpoint protection for businesses"),
    ("services/cyber-security-services/edr-security", "EDR endpoint detection and response"),
    ("services/cyber-security-services/network-security", "Network security services"),
    ("services/cyber-security-services/firewall-setup", "Firewall setup and configuration"),
    ("services/cyber-security-services/firewall-management", "Firewall management service"),
    ("services/cyber-security-services/email-security", "Email security and spam protection"),
    ("services/cyber-security-services/phishing-protection", "Phishing protection services"),
    ("services/cyber-security-services/security-monitoring", "24/7 security monitoring"),
    ("services/cybersecurity-services/security-audit", "Security audit and assessment"),
    ("services/cybersecurity-services/vulnerability-assessment", "Vulnerability assessment service"),
    ("services/cybersecurity-services/incident-response", "Cybersecurity incident response"),
    ("services/business-it-services/small-business-it-support", "Small business IT support"),
    ("services/cybersecurity-services/external-drive-recovery", "External drive recovery (security)"),
    ("services/business-it-services/it-consulting", "IT consulting services"),
    ("services/business-it-services/business-continuity", "Business continuity planning"),
    ("services/business-it-services/it-outsourcing", "IT outsourcing services"),
    ("services/business-it-services/office-it-setup", "Office IT setup and configuration"),
    ("services/computer-networking/wifi-setup", "WiFi setup and optimization"),
    ("services/computer-networking/router-setup", "Router setup and configuration"),
    ("services/computer-networking/network-troubleshooting", "Network troubleshooting service"),
    ("services/computer-networking/business-network-installation", "Business network installation"),
    ("services/computer-networking/network-security", "Network security setup"),
    ("services/computer-networking/network-upgrade", "Network upgrade service"),
    ("services/computer-networking/vpn-setup", "VPN setup for remote workers"),
    ("services/business-it-services/helpdesk-support", "IT helpdesk support"),
    ("services/business-it-services/server-management", "Server management services"),
    ("services/business-it-services/network-management", "Network management services"),
    ("services/business-it-services/it-maintenance", "IT maintenance and support plans"),
    ("services/business-it-services/microsoft-365-support", "Microsoft 365 setup and support"),
    ("services/business-it-services/email-setup", "Business email setup"),
    ("services/business-it-services/remote-work-setup", "Remote work IT setup"),
    ("services/phone-tablet-repair/iphone-repair", "iPhone repair services"),
    ("services/phone-tablet-repair/android-repair", "Android phone repair"),
    ("services/phone-tablet-repair/tablet-screen-repair", "Tablet screen repair"),
    ("services/phone-tablet-repair/phone-battery-replacement", "Phone battery replacement"),
    ("services/phone-tablet-repair/charging-port-repair", "Phone charging port repair"),
    ("services/phone-tablet-repair/phone-water-damage", "Phone water damage repair"),
    ("services/phone-tablet-repair/phone-data-recovery", "Phone data recovery"),
]

PROMPT_TEMPLATES = {
    "computer-repair": "Professional photo of a technician repairing a {detail} in a clean, well-lit computer repair shop. Modern workspace with tools and components visible. Blue and white color scheme. High quality, commercial photography style.",
    "laptop-repair": "Close-up professional photo of a technician working on a laptop {detail}. Clean repair bench, precision tools, bright lighting. Modern IT service center. Blue and white tones. Commercial photography.",
    "macbook-repair": "Professional photo of an Apple MacBook being repaired by a certified technician. {detail}. Clean white workspace, Apple-style minimalism. Blue accent lighting. High-end repair center.",
    "mac-mini-repair": "Professional photo of a Mac Mini being serviced. {detail}. Clean modern workspace, professional tools. Blue and white color scheme.",
    "imac-repair": "Professional photo of an iMac being repaired in a modern repair center. {detail}. Clean workspace with professional tools. Blue and white theme.",
    "data-recovery": "Professional photo showing data recovery process - {detail}. Clean room environment, specialized equipment, hard drives visible. Blue LED accents. Technical and professional atmosphere.",
    "cyber-security": "Professional illustration of cybersecurity concept - {detail}. Digital shield, lock icons, network protection visualization. Blue and dark theme. Modern, corporate style.",
    "business-it": "Professional photo of IT professionals providing {detail} in a modern office. Business casual attire, server room or office setting. Blue and white corporate style.",
    "networking": "Professional photo of network infrastructure - {detail}. Server rack, ethernet cables, network switches. Blue LED lighting. Clean, organized data center.",
    "phone-tablet": "Professional photo of a technician repairing a {detail}. Clean modern repair bench, precision tools, bright lighting. Mobile device repair center.",
    "general": "Professional photo representing {detail} by PC Plus Computing, a Vancouver BC IT company. Modern, clean, blue and white color scheme. Commercial photography style.",
}

def get_prompt_category(path):
    if "cyber-security" in path or "cybersecurity" in path:
        return "cyber-security"
    if "data-recovery" in path or "deleted-file" in path:
        return "data-recovery"
    if "macbook-repair" in path:
        return "macbook-repair"
    if "mac-mini-repair" in path:
        return "mac-mini-repair"
    if "imac-repair" in path:
        return "imac-repair"
    if "laptop-repair" in path:
        return "laptop-repair"
    if "computer-repair" in path:
        return "computer-repair"
    if "phone-tablet" in path:
        return "phone-tablet"
    if "business-it" in path:
        return "business-it"
    if "networking" in path or "network-setup" in path or "wifi" in path or "router" in path or "vpn" in path:
        return "networking"
    return "general"

def make_detail(path, description):
    slug = path.split("/")[-1]
    words = slug.replace("-", " ").replace("_", " ")
    return f"{words} - {description}"

def generate_prompt(path, description):
    category = get_prompt_category(path)
    template = PROMPT_TEMPLATES[category]
    detail = make_detail(path, description)
    prompt = template.format(detail=detail)
    prompt += " No text, no logos, no watermarks."
    return prompt

def create_folders_and_prompts():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    prompts = []
    for i, (path, desc) in enumerate(PAGES):
        folder = os.path.join(OUTPUT_DIR, path.replace("/", os.sep))
        os.makedirs(folder, exist_ok=True)
        prompt = generate_prompt(path, desc)
        prompts.append({
            "index": i + 1,
            "path": path,
            "folder": folder,
            "description": desc,
            "prompt": prompt,
            "filename": os.path.join(folder, "hero.png"),
        })
    with open("prompts.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["index", "path", "folder", "description", "prompt", "filename"])
        writer.writeheader()
        writer.writerows(prompts)
    print(f"Created {len(prompts)} folders under {OUTPUT_DIR}/")
    print(f"Prompts saved to prompts.csv")
    return prompts

def generate_with_openai(api_key, prompts, start_from=0, size="1792x1024"):
    generated = 0
    failed = 0
    for item in prompts:
        if item["index"] < start_from:
            continue
        if os.path.exists(item["filename"]) and os.path.getsize(item["filename"]) > 1000:
            print(f"  [{item['index']}/{len(prompts)}] SKIP (exists): {item['path']}")
            continue

        print(f"  [{item['index']}/{len(prompts)}] Generating: {item['path']}")
        try:
            payload = json.dumps({
                "model": "dall-e-3",
                "prompt": item["prompt"],
                "n": 1,
                "size": size,
                "quality": "standard",
                "response_format": "url"
            }).encode("utf-8")

            req = urllib.request.Request(
                "https://api.openai.com/v1/images/generations",
                data=payload,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {api_key}"
                }
            )
            with urllib.request.urlopen(req, timeout=120) as resp:
                result = json.loads(resp.read().decode())

            image_url = result["data"][0]["url"]
            img_req = urllib.request.Request(image_url)
            with urllib.request.urlopen(img_req, timeout=60) as img_resp:
                with open(item["filename"], "wb") as f:
                    f.write(img_resp.read())

            size_kb = os.path.getsize(item["filename"]) // 1024
            print(f"    Saved: {item['filename']} ({size_kb}KB)")
            generated += 1
            time.sleep(1)

        except urllib.error.HTTPError as e:
            body = e.read().decode() if e.fp else ""
            print(f"    FAILED: HTTP {e.code} - {body[:200]}")
            failed += 1
            if e.code == 429:
                print("    Rate limited, waiting 60s...")
                time.sleep(60)
            elif e.code == 401:
                print("    Invalid API key!")
                return generated, failed
        except Exception as e:
            print(f"    FAILED: {e}")
            failed += 1

    return generated, failed

def main():
    parser = argparse.ArgumentParser(description="PC Plus Computing Website Image Generator")
    parser.add_argument("--api-key", help="OpenAI API key for DALL-E 3")
    parser.add_argument("--prompts-only", action="store_true", help="Only create folders and prompts.csv")
    parser.add_argument("--start-from", type=int, default=0, help="Start from page number (for resuming)")
    parser.add_argument("--size", default="1792x1024", choices=["1024x1024", "1792x1024", "1024x1792"],
                        help="Image size (default: 1792x1024 landscape)")
    args = parser.parse_args()

    print("PC Plus Computing - Website Image Generator")
    print(f"Total pages: {len(PAGES)}")
    print()

    prompts = create_folders_and_prompts()

    if args.prompts_only:
        print("\nDone! Review prompts.csv and run with --api-key to generate images.")
        return

    if not args.api_key:
        print("\nNo API key provided. Run with --api-key YOUR_KEY to generate images.")
        print("Or use --prompts-only to just create the folder structure.")
        return

    print(f"\nStarting image generation with DALL-E 3...")
    print(f"Size: {args.size}")
    if args.start_from > 0:
        print(f"Resuming from page #{args.start_from}")
    print()

    generated, failed = generate_with_openai(args.api_key, prompts, args.start_from, args.size)
    print(f"\nDone! Generated: {generated}, Failed: {failed}")
    if failed > 0:
        print("Re-run with --start-from to resume failed items.")

if __name__ == "__main__":
    main()
