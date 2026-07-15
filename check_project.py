import subprocess
import sys
import os

def check_backend():
    print("====================================")
    print("Checking Backend (Python/Mypy)...")
    print("====================================")
    try:
        # Check if mypy is installed
        res = subprocess.run([sys.executable, "-m", "mypy", "--version"], capture_output=True, text=True)
        if res.returncode != 0:
            print("Mypy is not installed. Installing it now...")
            subprocess.run([sys.executable, "-m", "pip", "install", "mypy", "types-requests"], check=True)
        
        # Run mypy on backend directory
        print("Running: mypy backend/")
        mypy_res = subprocess.run([sys.executable, "-m", "mypy", "--ignore-missing-imports", "backend/"], text=True)
        
        if mypy_res.returncode == 0:
            print("[OK] Backend check passed!")
            return True
        else:
            print("[ERROR] Backend check failed.")
            return False
            
    except Exception as e:
        print(f"[ERROR] Failed to run backend check: {e}")
        return False

def check_frontend():
    print("\n====================================")
    print("Checking Frontend (TypeScript)...")
    print("====================================")
    frontend_dir = os.path.join(os.path.dirname(__file__), "frontend")
    
    # Use npx.cmd on windows
    npx_cmd = "npx.cmd" if os.name == 'nt' else "npx"
    npm_cmd = "npm.cmd" if os.name == 'nt' else "npm"
    
    try:
        # First ensure dependencies are installed
        if not os.path.exists(os.path.join(frontend_dir, "node_modules")):
            print("Installing frontend dependencies...")
            subprocess.run([npm_cmd, "install"], cwd=frontend_dir, check=True)
            
        print("Running: tsc --noEmit")
        tsc_res = subprocess.run([npx_cmd, "tsc", "--noEmit"], cwd=frontend_dir, text=True)
        
        if tsc_res.returncode == 0:
            print("[OK] Frontend check passed!")
            return True
        else:
            print("[ERROR] Frontend check failed.")
            return False
            
    except Exception as e:
        print(f"[ERROR] Failed to run frontend check: {e}")
        return False

def main():
    print("Starting Full Project Check...\n")
    backend_ok = check_backend()
    frontend_ok = check_frontend()
    
    print("\n====================================")
    print("Check Summary")
    print("====================================")
    print(f"Backend:  {'[PASS]' if backend_ok else '[FAIL]'}")
    print(f"Frontend: {'[PASS]' if frontend_ok else '[FAIL]'}")
    
    if backend_ok and frontend_ok:
        print("\nAll checks passed successfully! It is safe to commit or run.")
        sys.exit(0)
    else:
        print("\nSome checks failed. Please fix the errors above before proceeding.")
        sys.exit(1)

if __name__ == "__main__":
    main()
