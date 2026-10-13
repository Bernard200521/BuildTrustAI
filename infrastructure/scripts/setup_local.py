import os
import sys
import subprocess

def main():
    print("==================================================")
    print("      BuildTrust AI - Local Setup & Bootstrap    ")
    print("==================================================")

    # 1. Generate demo artifacts & data
    print("\n[Step 1/3] Generating sample artifacts & manifests...")
    subprocess.run([sys.executable, "infrastructure/scripts/generate_demo_evidence.py"], check=True)

    # 2. Train ML model
    print("\n[Step 2/3] Training local IsolationForest anomaly model...")
    subprocess.run([sys.executable, "-m", "backend.app.ml.train_model"], check=True)

    # 3. Seed demo releases
    print("\n[Step 3/3] Seeding demo projects and releases...")
    subprocess.run([sys.executable, "infrastructure/scripts/seed_demo.py"], check=True)

    print("\nSetup complete! You can now start the backend with:")
    print("  uvicorn backend.app.main:app --reload --port 8000")
    print("==================================================")

if __name__ == "__main__":
    main()
