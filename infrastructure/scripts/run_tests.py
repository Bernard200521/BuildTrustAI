import subprocess
import sys
import os

def main():
    print("==================================================")
    print("      BuildTrust AI - Test Suite Runner          ")
    print("==================================================")
    os.environ["PYTHONPATH"] = "."
    cmd = [sys.executable, "-m", "pytest", "backend/tests", "-v", "--tb=short"]
    result = subprocess.run(cmd)
    if result.returncode == 0:
        print("\nAll automated tests passed successfully!")
    else:
        print(f"\nTests finished with exit code {result.returncode}")
    sys.exit(result.returncode)

if __name__ == "__main__":
    main()
