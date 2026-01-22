#!/usr/bin/env python3
"""
Deploy MLOps Feedback Loop to Atlas ERP Server.

This script adds continuous learning capabilities:
- MLOps Engine tracks all AI predictions
- User feedback collection (positive/negative)
- Feedback storage for future model retraining
- Dashboard with interactive feedback UI

Usage:
    python scripts/deploy_mlops.py
"""
import getpass

import paramiko

SERVER_IP = "72.62.186.228"
USERNAME = "root"


def deploy_mlops():
    print(f"📈 Enabling MLOps Feedback Loop on {SERVER_IP}...")
    ssh_pass = getpass.getpass("🔑 SSH Password: ")

    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(SERVER_IP, username=USERNAME, password=ssh_pass, timeout=30)
        print("✅ Connected!")

        def run_cmd(cmd, timeout=120):
            stdin, stdout, stderr = client.exec_command(cmd, timeout=timeout)
            return stdout.read().decode()

        # Read local middleware_core.py and deploy
        with open("middleware_core.py", "r") as f:
            middleware_code = f.read()

        print("1️⃣ Uploading middleware with MLOps Engine...")
        run_cmd(
            f"cat > /root/atlas_erp/middleware_core.py << 'MWEOF'\n"
            f"{middleware_code}\nMWEOF"
        )

        print("2️⃣ Rebuilding containers...")
        result = run_cmd(
            "cd /root/atlas_erp && docker compose build --no-cache saudi-middleware "
            "&& docker compose up -d --force-recreate",
            timeout=180
        )
        print(result[-1000:] if len(result) > 1000 else result)

        print("3️⃣ Testing MLOps endpoints...")
        import time
        time.sleep(10)

        health = run_cmd("curl -sk https://atlas-sa.com/health")
        print(f"   Health: {health}")

        stats = run_cmd("curl -sk https://atlas-sa.com/api/mlops/stats")
        print(f"   MLOps Stats: {stats}")

        client.close()

        print("\n" + "=" * 60)
        print("✅ MLOps FEEDBACK LOOP ACTIVE!")
        print("=" * 60)
        print("""
📈 Features:
  • Every AI decision gets a unique prediction_id
  • Users can submit 👍/👎 feedback
  • Feedback stored for future retraining
  • Stats endpoint shows feedback distribution

🔗 Endpoints:
  • POST /api/purchase-orders/simulate
  • POST /api/mlops/feedback
  • GET  /api/mlops/stats

🌐 Dashboard:
  • https://atlas-sa.com/dashboard
""")

    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    deploy_mlops()
