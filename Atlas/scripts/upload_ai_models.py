#!/usr/bin/env python3
"""
Upload AI Model Assets to Atlas Server.

This script uploads trained ML models to the server for intent classification.

Expected files:
- intent_classifier_50k.pkl  -> /ai_core/models/
- intent_classifier_char.pkl -> /ai_core/models/
- clean_messages.csv         -> /ai_core/datasets/

Usage:
    python scripts/upload_ai_models.py
"""
import getpass
import os

import paramiko

SERVER_IP = "72.62.186.228"
USERNAME = "root"

# Files to upload (source -> destination)
MODEL_FILES = [
    ("intent_classifier_50k.pkl", "/root/atlas_erp/ai_core/models/"),
    ("intent_classifier_char.pkl", "/root/atlas_erp/ai_core/models/"),
]

DATASET_FILES = [
    ("clean_messages.csv", "/root/atlas_erp/ai_core/datasets/"),
]


def upload_ai_assets():
    print("🧠 Saudi AI Model Upload Tool")
    print("=" * 50)

    ssh_pass = getpass.getpass("🔑 Enter SSH Password: ")

    try:
        # Connect
        transport = paramiko.Transport((SERVER_IP, 22))
        transport.connect(username=USERNAME, password=ssh_pass)
        sftp = paramiko.SFTPClient.from_transport(transport)
        print("✅ Connected to server!")

        # Ensure directories exist
        print("\n📁 Checking directories...")
        for path in [
            "/root/atlas_erp/ai_core",
            "/root/atlas_erp/ai_core/models",
            "/root/atlas_erp/ai_core/datasets",
            "/root/atlas_erp/ai_core/logs"
        ]:
            try:
                sftp.mkdir(path)
                print(f"   Created: {path}")
            except IOError:
                pass  # Directory exists

        # Upload model files
        print("\n🚀 Uploading model files...")
        uploaded = 0
        for filename, dest_dir in MODEL_FILES:
            if os.path.exists(filename):
                dest_path = dest_dir + filename
                print(f"   📤 {filename} -> {dest_path}")
                sftp.put(filename, dest_path)
                uploaded += 1
            else:
                print(f"   ⚠️ {filename} not found (skipping)")

        # Upload dataset files
        print("\n📊 Uploading dataset files...")
        for filename, dest_dir in DATASET_FILES:
            if os.path.exists(filename):
                dest_path = dest_dir + filename
                print(f"   📤 {filename} -> {dest_path}")
                sftp.put(filename, dest_path)
                uploaded += 1
            else:
                print(f"   ⚠️ {filename} not found (skipping)")

        sftp.close()
        transport.close()

        print(f"\n✅ Upload complete! ({uploaded} files)")

        if uploaded > 0:
            print("\n🔄 Restarting middleware to load models...")
            # Reconnect to restart service
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(SERVER_IP, username=USERNAME, password=ssh_pass)
            stdin, stdout, stderr = client.exec_command(
                "cd /root/atlas_erp && docker compose restart saudi-middleware"
            )
            stdout.read()
            client.close()
            print("✅ Middleware restarted!")

            print("\n🧪 Verify model loaded:")
            print("   curl -sk https://atlas.xcircle.sa/health")

    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    upload_ai_assets()
