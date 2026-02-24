#!/usr/bin/env python3
"""
Version Checker - Verifică ce versiune de cod rulezi
"""

import sys
import os

print("=" * 60)
print("  Version Checker - WebRTC + MQTT")
print("=" * 60)
print()

# Check sender
sender_path = "sender/sender_mqtt.py"
if os.path.exists(sender_path):
    with open(sender_path, 'r') as f:
        content = f.read()
        
    print(f"Checking {sender_path}...")
    
    if "RTCConfiguration" in content and "ice_config" in content:
        print("  ❌ VERSIUNE VECHE (cu fix-ul prost ICE config)")
        print("  ⚠️  Aceasta este versiunea care NU merge!")
    elif "RTCPeerConnection()" in content:
        print("  ✅ VERSIUNE NOUĂ (simplă, fără ICE config)")
        print("  ✅ Aceasta ar trebui să meargă!")
    else:
        print("  ⚠️  NECUNOSCUT - verifică manual")
    
    # Check for UI fixes
    if "1.0" in content or "font.*1\\.0" in content:
        print("  ✅ Font overlay mărit (UI fix aplicat)")
    else:
        print("  ℹ️  Font overlay mic (fără UI fix)")
else:
    print(f"  ❌ {sender_path} not found!")

print()

# Check receiver
receiver_path = "receiver/receiver_gui_mqtt.py"
if os.path.exists(receiver_path):
    with open(receiver_path, 'r') as f:
        content = f.read()
        
    print(f"Checking {receiver_path}...")
    
    if "RTCConfiguration" in content and "ice_config" in content:
        print("  ❌ VERSIUNE VECHE (cu fix-ul prost ICE config)")
        print("  ⚠️  Aceasta este versiunea care NU merge!")
    elif "self.pc = RTCPeerConnection()" in content:
        print("  ✅ VERSIUNE NOUĂ (simplă, fără ICE config)")
        print("  ✅ Aceasta ar trebui să meargă!")
    else:
        print("  ⚠️  NECUNOSCUT - verifică manual")
    
    # Check for MQTT callback fix
    if "def _on_mqtt_message" in content:
        if "self.sensor_angle.set" in content:
            print("  ✅ MQTT callback funcțional (UI fix aplicat)")
        else:
            print("  ⚠️  MQTT callback gol (bug prezent)")
    
    # Check for log area size
    if "height=12" in content:
        print("  ✅ Log area mărită la 12 linii (UI fix aplicat)")
    elif "height=6" in content:
        print("  ℹ️  Log area mică (6 linii, fără UI fix)")
    
    # Check for Last Sent label
    if "last_command_label" in content:
        print("  ✅ 'Last Sent' label present (UI fix aplicat)")
    else:
        print("  ℹ️  'Last Sent' label absent (fără UI fix)")
else:
    print(f"  ❌ {receiver_path} not found!")

print()
print("=" * 60)
print("  REZUMAT")
print("=" * 60)

# Determine version
both_files = os.path.exists(sender_path) and os.path.exists(receiver_path)

if both_files:
    with open(sender_path, 'r') as f:
        sender_content = f.read()
    with open(receiver_path, 'r') as f:
        receiver_content = f.read()
    
    has_ice_config = ("RTCConfiguration" in sender_content or 
                     "RTCConfiguration" in receiver_content)
    has_ui_fixes = ("height=12" in receiver_content and 
                   "last_command_label" in receiver_content)
    
    if has_ice_config:
        print("❌ Rulezi VERSIUNEA 2 (cu fix-ul prost)")
        print("   Descarcă și instalează noua arhivă!")
    elif has_ui_fixes:
        print("✅ Rulezi VERSIUNEA 3 (corectă)")
        print("   Această versiune ar trebui să meargă!")
    else:
        print("⚠️  Posibil VERSIUNEA 1 (originală)")
        print("   Funcționează, dar fără UI fixes")
else:
    print("⚠️  Nu pot determina versiunea (fișiere lipsă)")

print()
print("Dacă vezi ❌ VERSIUNE VECHE:")
print("  1. Descarcă arhiva nouă (webrtc-streaming-mqtt.zip)")
print("  2. Dezarhivează")
print("  3. Copiază fișierele peste cele vechi")
print("  4. Rulează din nou acest script pentru verificare")
print()
