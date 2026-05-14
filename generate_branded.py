#!/usr/bin/env python3
"""
PC Plus Computing - Branded Service Image Generator
Uses OpenAI gpt-image-1 to generate branded 500x500 service images.
Generates at 1024x1024 then resizes to 500x500 for quality.

Usage:
  export OPENAI_API_KEY=your_key_here
  python generate_branded.py
  python generate_branded.py --start-from 50   # resume from page 50
  python generate_branded.py --dry-run          # show prompts only
"""

import os
import sys
import base64
import time
import argparse
import json
from PIL import Image
from io import BytesIO

try:
    from openai import OpenAI
except ImportError:
    print("Install openai: pip install openai pillow")
    sys.exit(1)

OUTPUT_DIR = "images"
FINAL_SIZE = 500
GEN_SIZE = "1024x1024"

BRAND_PROMPT = """Create a 500x500 branded service image for PC Plus Computing, a professional IT company in Vancouver BC.

Style requirements:
- Light themed: bright white and light blue color palette
- Professional, clean, modern marketing design
- Real-life professional technician action scene relevant to the service
- PC Plus Computing logo/branding at top left corner (blue cross/plus icon with "PC PLUS COMPUTING" text)
- Blue footer bar at bottom with: www.pcpluscomputing.com and phone icon 604-760-1662
- Bold service title text, clean and readable
- Include 3-4 relevant service bullet points with checkmark icons
- Professional computer repair / IT support marketing card style
- No extra paragraphs or unnecessary text
- High quality, commercial design look
"""

PAGES = [
    ("homepage", "PC Plus Computing", "Full-Service IT Company", ["Computer Repair", "Cybersecurity", "Network Solutions", "Data Recovery"]),
    ("about", "About PC Plus Computing", "Your Trusted IT Partner", ["Certified Technicians", "Years of Experience", "Customer Focused", "Local Vancouver Team"]),
    ("appointments", "Book An Appointment", "Schedule Your Service", ["Same-Day Service", "Flexible Hours", "Free Estimates", "Walk-ins Welcome"]),
    ("contact-us", "Contact Us", "Get In Touch Today", ["Phone Support", "Email Support", "Walk-in Service", "Remote Assistance"]),
    ("services/backup-disaster-recovery", "Backup & Disaster Recovery", "Protect Your Business Data", ["Automated Backups", "Cloud Storage", "Disaster Recovery Plans", "Business Continuity"]),
    ("services/business-it-services", "Business IT Services", "Empowering Business with Reliable IT", ["Managed IT Services", "IT Support & Monitoring", "Cloud Solutions", "IT Consulting"]),
    ("services/cloud-migration", "Cloud Migration", "Move Your Business to the Cloud", ["Microsoft 365 Migration", "Data Transfer", "Cloud Setup", "Ongoing Support"]),
    ("services/computer-networking", "Computer Networking", "Network Setup & Configuration", ["Network Design", "Wi-Fi Optimization", "Troubleshooting", "Secure Connections"]),
    ("services/computer-repair", "Computer Repair Services", "Fast, Reliable & Professional", ["Diagnostics & Repair", "Hardware & Software", "Virus Removal", "Performance Tune-Up"]),
    ("services/computer-repair/computer-diagnostics", "Computer Diagnostics", "Find the Problem Fast", ["Hardware Testing", "Software Analysis", "Performance Check", "Full System Report"]),
    ("services/computer-repair/custom-pc-build", "Custom PC Build", "Built To Your Specifications", ["Gaming PCs", "Workstations", "Budget Builds", "Component Selection"]),
    ("services/computer-repair/desktop-repair", "Desktop Computer Repair", "Expert Desktop Service", ["No Power Fix", "Crashing Repair", "Hardware Errors", "System Restore"]),
    ("services/computer-repair/gaming-computer-repair", "Gaming Computer Repair", "Get Back in the Game", ["GPU Troubleshooting", "Overheating Fix", "Performance Tuning", "Upgrade Service"]),
    ("services/computer-repair/hardware-repair", "Hardware Repair", "Component Level Repair", ["Motherboard Repair", "Power Supply Fix", "RAM Upgrade", "Storage Repair"]),
    ("services/computer-repair/linux-repair", "Linux Repair", "Expert Linux Support", ["Ubuntu & Debian", "Server Administration", "Driver Issues", "System Recovery"]),
    ("services/computer-repair/motherboard-repair", "Motherboard Repair", "Board Level Diagnostics", ["Component Repair", "Capacitor Replace", "BIOS Recovery", "Socket Repair"]),
    ("services/computer-repair/password-recovery", "Password Recovery", "Regain Access Safely", ["Windows Password", "BIOS Password", "Account Recovery", "Data Preserved"]),
    ("services/computer-repair/pc-upgrade", "PC Upgrade", "Boost Your Performance", ["SSD Upgrade", "RAM Upgrade", "GPU Upgrade", "Full System Refresh"]),
    ("services/computer-repair/server-repair", "Server Repair", "Keep Your Business Running", ["Hardware Diagnostics", "RAID Recovery", "OS Repair", "Preventive Maintenance"]),
    ("services/computer-repair/slow-computer-fix", "Slow Computer Fix", "Speed Up Your PC", ["Startup Optimization", "Malware Cleanup", "Disk Cleanup", "Hardware Check"]),
    ("services/computer-repair/software-repair", "Software Repair", "Fix Software Issues", ["OS Reinstall", "Driver Fix", "App Troubleshoot", "Update Errors"]),
    ("services/computer-repair/windows-repair", "Windows Repair", "Windows Expert Service", ["Blue Screen Fix", "Boot Repair", "Registry Cleanup", "Update Issues"]),
    ("services/cyber-security-services", "Cybersecurity Services", "Protect Your Digital Assets", ["Endpoint Protection", "Threat Detection", "Ransomware Protection", "Security Audits"]),
    ("services/data-recovery", "Data Recovery Services", "We Recover What Matters Most", ["Hard Drive Recovery", "SSD Recovery", "Deleted Files", "RAID Recovery"]),
    ("services/imac-repair", "iMac Repair", "Certified Apple Service", ["Screen Repair", "Hard Drive Upgrade", "OS Repair", "Performance Fix"]),
    ("services/it-support", "IT Support", "Help When You Need It", ["Remote Support", "On-Site Service", "Phone Support", "Managed IT"]),
    ("services/laptop-repair", "Laptop Repair Services", "We Fix All Major Brands", ["Screen Repair", "Battery Replacement", "Motherboard Repair", "Software Solutions"]),
    ("services/mac-mini-repair", "Mac Mini Repair", "Expert Mac Mini Service", ["RAM Upgrade", "Storage Upgrade", "OS Repair", "Diagnostics"]),
    ("services/macbook-repair", "MacBook Repair", "Professional MacBook Service", ["Screen Repair", "Battery Replace", "Keyboard Fix", "Data Recovery"]),
    ("services/managed-it-services", "Managed IT Services", "Complete IT Management", ["24/7 Monitoring", "Patch Management", "Help Desk", "Strategic Planning"]),
    ("services/network-setup", "Network Setup", "Professional Installation", ["Wired & Wireless", "Router Config", "Security Setup", "Performance Tuning"]),
    ("services/on-site-computer-support", "Onsite Computer Support", "We Come To You", ["Same-Day Service", "Business Support", "Home Service", "Emergency Calls"]),
    ("services/onsite-computer-support", "Onsite Support", "On-Location IT Service", ["Quick Response", "Business Visits", "Residential Support", "Setup & Install"]),
    ("services/phone-tablet-repair", "Phone & Tablet Repair", "Mobile Device Experts", ["Screen Repair", "Battery Replace", "Charging Port Fix", "Data Recovery"]),
    ("services/remote-support", "Remote Support", "Fast Remote Assistance", ["24/7 Support", "Remote Access", "Problem Resolution", "Support You Can Trust"]),
    ("services/seo-services", "SEO Services", "Grow Your Online Presence", ["Keyword Research", "On-Page SEO", "Local SEO", "Performance Reports"]),
    ("services/virus-removal", "Virus & Malware Removal", "Protect Your Device & Data", ["Virus Removal", "Malware Protection", "System Security", "Real-Time Protection"]),
    ("services/website-design", "Website Design", "Professional Web Solutions", ["Custom Design", "Mobile Responsive", "SEO Friendly", "E-Commerce Ready"]),
    ("services/computer-repair/power-supply-repair", "Power Supply Repair", "Reliable Power Solutions", ["PSU Testing", "Replacement", "Surge Protection", "Cable Management"]),
    ("services/laptop-repair/laptop-screen-repair", "Laptop Screen Repair", "Crystal Clear Display", ["LCD Replacement", "LED Screen Fix", "Touchscreen Repair", "Same-Day Service"]),
    ("services/laptop-repair/laptop-battery-replacement", "Laptop Battery Replacement", "Restore Battery Life", ["All Brands", "Genuine Parts", "Quick Install", "Battery Test"]),
    ("services/computer-repair/overheating-fix", "Overheating Fix", "Cool Down Your System", ["Thermal Paste", "Fan Cleaning", "Heatsink Check", "Airflow Optimization"]),
    ("services/laptop-repair/laptop-charging-port-repair", "Charging Port Repair", "Restore Your Power Connection", ["Port Replacement", "Connector Fix", "Cable Check", "Soldering Repair"]),
    ("services/computer-repair/boot-error-repair", "Boot Error Repair", "Get Your PC Starting Again", ["Blue Screen Fix", "Boot Loop Repair", "MBR Recovery", "OS Reinstall"]),
    ("services/laptop-repair/laptop-water-damage-repair", "Water Damage Repair", "Save Your Laptop", ["Component Cleaning", "Corrosion Removal", "Board Repair", "Data Recovery"]),
    ("services/laptop-repair/laptop-keyboard-repair", "Laptop Keyboard Repair", "Type With Confidence", ["Key Replacement", "Full Keyboard Swap", "Spill Damage Fix", "All Brands"]),
    ("services/laptop-repair/gaming-laptop-repair", "Gaming Laptop Repair", "Back In The Game", ["GPU Repair", "Overheating Fix", "Screen Upgrade", "Performance Boost"]),
    ("services/computer-repair/system-optimization", "System Optimization", "Maximum Performance", ["Startup Speed", "Memory Cleanup", "Registry Fix", "Driver Updates"]),
    ("services/laptop-repair/gaming-laptop-upgrade", "Gaming Laptop Upgrade", "Level Up Your Setup", ["RAM Upgrade", "SSD Install", "Thermal Mods", "Software Tuning"]),
    ("services/data-recovery/phone-data-recovery", "Phone Data Recovery", "Recover Lost Phone Data", ["Photos & Videos", "Contacts Recovery", "Message Recovery", "All Phone Brands"]),
    ("services/laptop-repair/laptop-boot-issue", "Laptop Boot Issue", "Fix Startup Problems", ["Boot Loop Fix", "OS Recovery", "BIOS Repair", "Drive Check"]),
    ("services/macbook-repair/macbook-screen-repair", "MacBook Screen Repair", "Retina Display Expert", ["Retina Display", "LCD Replacement", "Backlight Fix", "Quick Turnaround"]),
    ("services/macbook-repair/macbook-ssd-upgrade", "MacBook SSD Upgrade", "Faster Storage Solution", ["Speed Boost", "Data Migration", "All Models", "Warranty Service"]),
    ("services/data-recovery/server-data-recovery", "Server Data Recovery", "Business Data Rescue", ["RAID Recovery", "Database Recovery", "VM Recovery", "24/7 Emergency"]),
    ("services/macbook-repair/macbook-os-repair", "MacBook OS Repair", "macOS Expert Service", ["OS Reinstall", "Update Issues", "Recovery Mode", "Data Preserved"]),
    ("services/macbook-repair/macbook-battery-replacement", "MacBook Battery Replacement", "New Battery New Life", ["Genuine Parts", "All Models", "Quick Service", "Battery Health"]),
    ("services/macbook-repair/macbook-keyboard-repair", "MacBook Keyboard Repair", "Butterfly & Magic Keyboard", ["Key Replacement", "Full Top Case", "Spill Repair", "All Models"]),
    ("services/data-recovery/raid-data-recovery", "RAID Data Recovery", "Multi-Disk Recovery Expert", ["RAID 0/1/5/6", "Controller Failure", "Rebuild Errors", "Server RAID"]),
    ("services/macbook-repair/macbook-data-recovery", "MacBook Data Recovery", "Recover Your Mac Data", ["Drive Failure", "Deleted Files", "T2 Chip Recovery", "Time Machine Fix"]),
    ("services/imac-repair/imac-screen-repair", "iMac Screen Repair", "Stunning Display Restored", ["Retina 4K/5K", "LCD Replacement", "Glass Repair", "Calibration"]),
    ("services/macbook-repair/macbook-pro-repair", "MacBook Pro Repair", "Pro Level Service", ["Touch Bar Fix", "GPU Repair", "Logic Board", "All Pro Models"]),
    ("services/data-recovery/nas-data-recovery", "NAS Data Recovery", "Network Storage Recovery", ["Synology Recovery", "QNAP Recovery", "Multi-Bay RAID", "Business NAS"]),
    ("services/imac-repair/imac-hard-drive-replacement", "iMac Hard Drive Replacement", "Upgrade Your iMac Storage", ["SSD Upgrade", "Fusion Drive Fix", "Data Migration", "Speed Boost"]),
    ("services/laptop-repair/laptop-overheating-fix", "Laptop Overheating Fix", "Keep It Cool", ["Fan Cleaning", "Thermal Paste", "Vent Cleaning", "Cooling Pad Advice"]),
    ("services/laptop-repair/laptop-slow-performance", "Slow Laptop Fix", "Speed Up Your Laptop", ["RAM Upgrade", "SSD Install", "Malware Removal", "System Cleanup"]),
    ("services/laptop-repair/laptop-motherboard-repair", "Laptop Motherboard Repair", "Board Level Expert", ["Component Repair", "Soldering", "Power Circuit", "Chip Replacement"]),
    ("services/laptop-repair/laptop-hinge-repair", "Laptop Hinge Repair", "Sturdy Hinge Restoration", ["Hinge Replacement", "Housing Repair", "Bracket Fix", "All Brands"]),
    ("services/laptop-repair/laptop-fan-repair", "Laptop Fan Repair", "Silent Cooling Restored", ["Fan Replacement", "Noise Fix", "Bearing Service", "Thermal Check"]),
    ("services/laptop-repair/laptop-diagnostics", "Laptop Diagnostics", "Complete System Check", ["Hardware Test", "Software Scan", "Battery Health", "Full Report"]),
    ("services/laptop-repair/laptop-software-repair", "Laptop Software Repair", "Fix Software Issues", ["OS Reinstall", "Driver Fix", "Virus Clean", "App Errors"]),
    ("services/laptop-repair/laptop-hard-drive-replacement", "Hard Drive Replacement", "New Drive New Speed", ["HDD to SSD", "Data Migration", "All Brands", "Quick Install"]),
    ("services/laptop-repair/laptop-ssd-upgrade", "Laptop SSD Upgrade", "Instant Speed Boost", ["NVMe SSD", "Data Clone", "All Laptops", "Same-Day Service"]),
    ("services/mac-mini-repair/mac-mini-upgrade", "Mac Mini Upgrade", "More Power More Storage", ["RAM Upgrade", "SSD Upgrade", "Performance Boost", "All Models"]),
    ("services/macbook-repair/macbook-overheating", "MacBook Overheating Fix", "Keep Your Mac Cool", ["Fan Service", "Thermal Paste", "Vent Clean", "SMC Reset"]),
    ("services/mac-mini-repair/mac-mini-diagnostics", "Mac Mini Diagnostics", "Full System Analysis", ["Hardware Check", "Software Scan", "Performance Test", "Detailed Report"]),
    ("services/macbook-repair/macbook-slow-performance", "MacBook Slow Performance", "Speed Up Your Mac", ["SSD Upgrade", "RAM Boost", "OS Cleanup", "App Optimization"]),
    ("services/macbook-repair/macbook-diagnostics", "MacBook Diagnostics", "Complete Mac Checkup", ["Hardware Test", "Battery Health", "Storage Check", "System Report"]),
    ("services/data-recovery/hard-drive-data-recovery", "Hard Drive Recovery", "Save Your Precious Data", ["Mechanical Failure", "Head Crash", "Bad Sectors", "Clean Room"]),
    ("deleted-file-recovery", "Deleted File Recovery", "Get Your Files Back", ["Accidental Delete", "Emptied Recycle Bin", "Format Recovery", "All File Types"]),
    ("services/data-recovery/ssd-data-recovery", "SSD Data Recovery", "Flash Storage Recovery", ["NAND Recovery", "Controller Failure", "Trim Recovery", "All SSD Brands"]),
    ("services/data-recovery/usb-data-recovery", "USB Data Recovery", "Flash Drive Rescue", ["Broken USB", "Corrupted Drive", "Deleted Files", "All Capacities"]),
    ("services/data-recovery/formatted-drive-recovery", "Formatted Drive Recovery", "Recover After Format", ["Quick Format", "Full Format", "Partition Recovery", "All File Systems"]),
    ("services/data-recovery/water-damaged-drive", "Water Damaged Drive", "Wet Drive Recovery", ["Flood Damage", "Spill Damage", "Corrosion Repair", "Emergency Service"]),
    ("services/data-recovery/emergency-data-recovery", "Emergency Data Recovery", "24/7 Urgent Recovery", ["Same-Day Service", "Priority Queue", "All Media Types", "Rush Delivery"]),
    ("services/data-recovery/external-drive-recovery", "External Drive Recovery", "Portable Drive Rescue", ["USB Drives", "Portable HDD", "Thunderbolt", "All Brands"]),
    ("services/cyber-security-services/endpoint-protection", "Endpoint Protection", "Secure Every Device", ["Antivirus", "Anti-Malware", "Real-Time Scanning", "Central Management"]),
    ("services/cyber-security-services/edr-security", "EDR Security", "Advanced Threat Detection", ["Behavior Analysis", "Threat Hunting", "Incident Response", "24/7 Monitoring"]),
    ("services/cyber-security-services/network-security", "Network Security", "Protect Your Network", ["Firewall Setup", "IDS/IPS", "VPN Security", "Access Control"]),
    ("services/cyber-security-services/firewall-setup", "Firewall Setup", "Strong Perimeter Defense", ["Hardware Firewall", "Software Firewall", "Rule Configuration", "Traffic Analysis"]),
    ("services/cyber-security-services/firewall-management", "Firewall Management", "Ongoing Protection", ["Rule Updates", "Log Monitoring", "Threat Blocking", "Performance Tuning"]),
    ("services/cyber-security-services/email-security", "Email Security", "Protect Your Inbox", ["Spam Filtering", "Phishing Block", "Encryption", "Attachment Scan"]),
    ("services/cyber-security-services/phishing-protection", "Phishing Protection", "Stop Phishing Attacks", ["Email Filtering", "Link Scanning", "User Training", "Threat Alerts"]),
    ("services/cyber-security-services/security-monitoring", "Security Monitoring", "24/7 Watchful Protection", ["Real-Time Alerts", "Log Analysis", "Threat Detection", "Incident Response"]),
    ("services/cybersecurity-services/security-audit", "Security Audit", "Know Your Vulnerabilities", ["Network Scan", "Policy Review", "Compliance Check", "Risk Assessment"]),
    ("services/cybersecurity-services/vulnerability-assessment", "Vulnerability Assessment", "Find Weaknesses First", ["Penetration Testing", "System Scan", "Risk Report", "Remediation Plan"]),
    ("services/cybersecurity-services/incident-response", "Incident Response", "Fast Action When Breached", ["Threat Containment", "Forensic Analysis", "System Recovery", "Prevention Plan"]),
    ("services/business-it-services/small-business-it-support", "Small Business IT Support", "IT For Growing Businesses", ["Help Desk", "Network Support", "Backup Setup", "Security"]),
    ("services/cybersecurity-services/external-drive-recovery", "External Drive Recovery", "Secure Drive Recovery", ["Encrypted Drives", "Forensic Recovery", "Chain of Custody", "All Brands"]),
    ("services/business-it-services/it-consulting", "IT Consulting", "Strategic IT Guidance", ["Technology Planning", "Budget Optimization", "Vendor Management", "Growth Strategy"]),
    ("services/business-it-services/business-continuity", "Business Continuity", "Keep Business Running", ["Disaster Planning", "Backup Strategy", "Failover Setup", "Recovery Testing"]),
    ("services/business-it-services/it-outsourcing", "IT Outsourcing", "Your Virtual IT Department", ["Cost Savings", "Expert Team", "Scalable Support", "24/7 Coverage"]),
    ("services/business-it-services/office-it-setup", "Office IT Setup", "Complete Office Technology", ["Workstation Setup", "Network Install", "Printer Config", "Phone System"]),
    ("services/computer-networking/wifi-setup", "Wi-Fi Setup", "Strong Wireless Coverage", ["Router Setup", "Range Extenders", "Mesh Network", "Security Config"]),
    ("services/computer-networking/router-setup", "Router Setup", "Optimal Network Config", ["Port Forwarding", "QoS Setup", "Firmware Update", "Security Settings"]),
    ("services/computer-networking/network-troubleshooting", "Network Troubleshooting", "Fix Connection Issues", ["Speed Testing", "Packet Analysis", "DNS Issues", "Hardware Check"]),
    ("services/computer-networking/business-network-installation", "Business Network Install", "Enterprise Grade Networks", ["Structured Cabling", "Switch Config", "VLAN Setup", "Scalable Design"]),
    ("services/computer-networking/network-security", "Network Security", "Secure Your Network", ["Firewall Config", "Access Control", "Encryption", "Monitoring"]),
    ("services/computer-networking/network-upgrade", "Network Upgrade", "Faster Better Network", ["Speed Upgrade", "Equipment Refresh", "Cable Upgrade", "Capacity Planning"]),
    ("services/computer-networking/vpn-setup", "VPN Setup", "Secure Remote Access", ["Site-to-Site VPN", "Remote Workers", "Split Tunneling", "Always-On VPN"]),
    ("services/business-it-services/helpdesk-support", "Helpdesk Support", "IT Help When You Need It", ["Ticket System", "Remote Fix", "Phone Support", "Quick Resolution"]),
    ("services/business-it-services/server-management", "Server Management", "Reliable Server Operations", ["Monitoring", "Patch Management", "Backup Config", "Performance Tuning"]),
    ("services/business-it-services/network-management", "Network Management", "Proactive Network Care", ["Traffic Monitoring", "Device Management", "Firmware Updates", "Capacity Planning"]),
    ("services/business-it-services/it-maintenance", "IT Maintenance", "Prevent Problems Before They Start", ["Regular Checkups", "System Updates", "Hardware Checks", "Performance Reports"]),
    ("services/business-it-services/microsoft-365-support", "Microsoft 365 Support", "Expert M365 Help", ["Email Setup", "Teams Config", "SharePoint", "License Management"]),
    ("services/business-it-services/email-setup", "Email Setup", "Professional Business Email", ["Domain Email", "Migration", "Spam Filter", "Mobile Access"]),
    ("services/business-it-services/remote-work-setup", "Remote Work Setup", "Work From Anywhere", ["VPN Access", "Cloud Setup", "Video Conferencing", "Security Tools"]),
    ("services/phone-tablet-repair/iphone-repair", "iPhone Repair", "Expert iPhone Service", ["Screen Repair", "Battery Replace", "Camera Fix", "Charging Port"]),
    ("services/phone-tablet-repair/android-repair", "Android Repair", "All Android Brands", ["Screen Repair", "Battery Replace", "Software Fix", "Water Damage"]),
    ("services/phone-tablet-repair/tablet-screen-repair", "Tablet Screen Repair", "Touch Screen Experts", ["iPad Repair", "Android Tablet", "Digitizer Fix", "Glass Replace"]),
    ("services/phone-tablet-repair/phone-battery-replacement", "Phone Battery Replacement", "Restore Battery Life", ["Same-Day Service", "All Brands", "Genuine Parts", "Battery Test"]),
    ("services/phone-tablet-repair/charging-port-repair", "Charging Port Repair", "Fix Your Charging", ["Port Replace", "Cable Check", "Wireless Charging", "Quick Fix"]),
    ("services/phone-tablet-repair/phone-water-damage", "Phone Water Damage", "Save Your Wet Phone", ["Component Cleaning", "Corrosion Removal", "Board Repair", "Data Recovery"]),
    ("services/phone-tablet-repair/phone-data-recovery", "Phone Data Recovery", "Rescue Phone Data", ["Photo Recovery", "Contact Restore", "Message Recovery", "Broken Phone"]),
]

def generate_image(client, service_title, tagline, bullets, output_path, index, total):
    bullet_text = "\n".join([f"- {b}" for b in bullets])
    prompt = f"""{BRAND_PROMPT}
Main title: {service_title}
Subtitle: {tagline}
Bullet points:
{bullet_text}
"""
    print(f"  [{index}/{total}] Generating: {service_title}")

    try:
        result = client.images.generate(
            model="gpt-image-1",
            prompt=prompt,
            size=GEN_SIZE,
            quality="medium",
        )

        image_base64 = result.data[0].b64_json
        image_bytes = base64.b64decode(image_base64)
        img = Image.open(BytesIO(image_bytes))
        img = img.resize((FINAL_SIZE, FINAL_SIZE), Image.LANCZOS)

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        img.save(output_path, "PNG", optimize=True)

        size_kb = os.path.getsize(output_path) // 1024
        print(f"    Saved: {output_path} ({size_kb}KB)")
        return True

    except Exception as e:
        print(f"    FAILED: {e}")
        if "rate_limit" in str(e).lower() or "429" in str(e):
            print("    Rate limited, waiting 60s...")
            time.sleep(60)
        return False

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--start-from", type=int, default=1, help="Resume from page number")
    parser.add_argument("--dry-run", action="store_true", help="Show prompts only")
    args = parser.parse_args()

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key and not args.dry_run:
        print("Set OPENAI_API_KEY environment variable first:")
        print("  export OPENAI_API_KEY=sk-...")
        sys.exit(1)

    print(f"PC Plus Computing - Branded Image Generator")
    print(f"Total pages: {len(PAGES)}")
    print(f"Output: {FINAL_SIZE}x{FINAL_SIZE} PNG")
    print(f"Generate at: {GEN_SIZE}, resize down for quality")
    print()

    if args.dry_run:
        for i, (path, title, tagline, bullets) in enumerate(PAGES, 1):
            print(f"[{i}] {path}")
            print(f"    Title: {title}")
            print(f"    Tagline: {tagline}")
            print(f"    Bullets: {', '.join(bullets)}")
            print()
        print("Done! Run without --dry-run to generate images.")
        return

    client = OpenAI(api_key=api_key)
    total = len(PAGES)
    success = 0
    failed = 0

    for i, (path, title, tagline, bullets) in enumerate(PAGES, 1):
        if i < args.start_from:
            continue

        output_path = os.path.join(OUTPUT_DIR, path.replace("/", os.sep), "hero.png")
        if os.path.exists(output_path) and os.path.getsize(output_path) > 5000:
            print(f"  [{i}/{total}] SKIP (exists): {path}")
            continue

        ok = generate_image(client, title, tagline, bullets, output_path, i, total)
        if ok:
            success += 1
        else:
            failed += 1
        time.sleep(2)

    print(f"\nDone! Success: {success}, Failed: {failed}")
    if failed > 0:
        print(f"Re-run with --start-from to retry failed images.")

    progress_file = "progress.json"
    with open(progress_file, "w") as f:
        json.dump({"total": total, "success": success, "failed": failed}, f)

if __name__ == "__main__":
    main()
