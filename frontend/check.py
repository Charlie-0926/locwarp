import subprocess
import os
import sys

def main():
    cwd = r"c:\Users\Charlie\Downloads\locwarp-main\frontend"
    # use npm run typecheck or something, let's try finding npm first
    npm_path = "npm.cmd"
    try:
        res = subprocess.run([npm_path, "run", "build"], cwd=cwd, capture_output=True, text=True, shell=True)
        print("STDOUT:", res.stdout)
        print("STDERR:", res.stderr)
        print("CODE:", res.returncode)
    except Exception as e:
        print("ERR:", e)

    try:
        res = subprocess.run(["npx.cmd", "tsc", "--noEmit"], cwd=cwd, capture_output=True, text=True, shell=True)
        print("STDOUT:", res.stdout)
        print("STDERR:", res.stderr)
        print("CODE:", res.returncode)
    except Exception as e:
        print("ERR:", e)

if __name__ == "__main__":
    main()
