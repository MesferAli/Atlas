#!/usr/bin/env python3
"""
Atlas Interactive Chat - Test Data Moat Security
Query the Oracle schema with role-based access control.
"""

import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer

# Configuration
COLLECTION_NAME = "oracle_schema"
QDRANT_PATH = os.getenv("ATLAS_QDRANT_PATH", "./qdrant_data")

# Role hierarchy (higher includes lower)
ROLE_HIERARCHY = {
    "PUBLIC": 0,
    "PER_EMPLOYEE_ROLE": 1,
    "LINE_MANAGER_ROLE": 2,
    "PROCUREMENT_MANAGER_ROLE": 3,
    "PAYROLL_MANAGER_ROLE": 4,
    "PAYROLL_ADMIN_ROLE": 5,
    "HR_ADMIN_ROLE": 6,
    "SYSTEM_ADMIN": 10,
}

# Classification sensitivity levels
CLASSIFICATION_LEVELS = {
    "PUBLIC": 0,
    "INTERNAL": 1,
    "RESTRICTED": 2,
    "SECRET": 3,
    "TOP_SECRET": 4,
}


def check_access(user_role: str, required_role: str, classification: str) -> tuple[bool, str]:
    """
    Check if user has access based on role and classification.
    Returns (allowed, reason).
    """
    user_level = ROLE_HIERARCHY.get(user_role, 0)
    required_level = ROLE_HIERARCHY.get(required_role, 0)

    if user_level < required_level:
        return False, f"🚫 ACCESS DENIED: Requires '{required_role}' (you have '{user_role}')"

    # Additional check for SECRET/TOP_SECRET
    class_level = CLASSIFICATION_LEVELS.get(classification, 0)
    if class_level >= 3 and user_role not in ["PAYROLL_MANAGER_ROLE", "PAYROLL_ADMIN_ROLE", "HR_ADMIN_ROLE", "SYSTEM_ADMIN"]:
        return False, f"🔴 BLOCKED: '{classification}' data requires elevated privileges"

    return True, "✅ ACCESS GRANTED"


def search_schema(client: QdrantClient, model: SentenceTransformer, query: str, user_role: str, limit: int = 5):
    """Search schema with role-based filtering."""

    # Generate query embedding
    query_vector = model.encode(query).tolist()

    # Search Qdrant
    results = client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_vector,
        limit=limit,
    )

    print(f"\n🔍 Search: \"{query}\"")
    print(f"👤 Your Role: {user_role}")
    print("=" * 60)

    accessible = []
    blocked = []

    for i, result in enumerate(results.points, 1):
        payload = result.payload
        name = payload.get("name", "Unknown")
        obj_type = payload.get("type", "Unknown")
        classification = payload.get("classification", "INTERNAL")
        required_role = payload.get("min_required_role", "PUBLIC")
        description = payload.get("description", "")[:50]

        allowed, reason = check_access(user_role, required_role, classification)

        entry = {
            "name": name,
            "type": obj_type,
            "classification": classification,
            "required_role": required_role,
            "description": description,
            "score": result.score,
        }

        if allowed:
            accessible.append(entry)
        else:
            blocked.append((entry, reason))

    # Print accessible results
    if accessible:
        print(f"\n✅ Accessible Results ({len(accessible)}):")
        for entry in accessible:
            cls_icon = {"INTERNAL": "🟢", "RESTRICTED": "🟠", "SECRET": "🔴"}.get(entry["classification"], "⚪")
            print(f"  {cls_icon} {entry['type']}: {entry['name']}")
            print(f"     Classification: {entry['classification']} | Score: {entry['score']:.3f}")
            print(f"     {entry['description']}...")

    # Print blocked results
    if blocked:
        print(f"\n🚫 Blocked Results ({len(blocked)}):")
        for entry, reason in blocked:
            print(f"  🔒 {entry['type']}: {entry['name']}")
            print(f"     {reason}")

    return accessible, blocked


def interactive_mode():
    """Run interactive chat mode."""

    print("\n" + "=" * 60)
    print("🏛️  ATLAS - Saudi AI Middleware for Oracle Fusion")
    print("    Data Moat Security Demo")
    print("=" * 60)

    # Initialize
    print("\n⏳ Loading components...")

    # Try workspace path first (RunPod), then local path
    qdrant_path = "/workspace/Atlas/qdrant_data"
    if not Path(qdrant_path).exists():
        qdrant_path = QDRANT_PATH

    client = QdrantClient(path=qdrant_path)

    # Set HF_ENDPOINT for mirror if needed
    if os.getenv("HF_ENDPOINT"):
        print(f"  Using HF Mirror: {os.getenv('HF_ENDPOINT')}")

    model = SentenceTransformer("all-MiniLM-L6-v2")
    print("✅ Ready!\n")

    # Available roles
    roles = list(ROLE_HIERARCHY.keys())

    print("📋 Available Roles:")
    for i, role in enumerate(roles, 1):
        print(f"  {i}. {role}")

    # Select role
    print("\n👤 Select your role (enter number or name):")
    role_input = input("   > ").strip()

    try:
        role_idx = int(role_input) - 1
        user_role = roles[role_idx]
    except (ValueError, IndexError):
        user_role = role_input if role_input in roles else "PER_EMPLOYEE_ROLE"

    print(f"\n✅ Role set to: {user_role}")
    print("\n💡 Type your question (or 'quit' to exit, 'role' to change role)")
    print("-" * 60)

    while True:
        try:
            query = input("\n🗣️  You: ").strip()

            if not query:
                continue

            if query.lower() in ["quit", "exit", "q"]:
                print("\n👋 Goodbye!")
                break

            if query.lower() == "role":
                print("\n📋 Available Roles:")
                for i, role in enumerate(roles, 1):
                    marker = "→" if role == user_role else " "
                    print(f"  {marker} {i}. {role}")
                role_input = input("   Select: ").strip()
                try:
                    role_idx = int(role_input) - 1
                    user_role = roles[role_idx]
                    print(f"✅ Role changed to: {user_role}")
                except (ValueError, IndexError):
                    print("❌ Invalid selection")
                continue

            # Search with role-based access
            search_schema(client, model, query, user_role)

        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    interactive_mode()
