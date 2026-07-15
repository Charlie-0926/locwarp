import subprocess

def main():
    try:
        res = subprocess.run(["python", "-m", "mypy", "backend/"], cwd=r"c:\Users\Charlie\Downloads\locwarp-main", capture_output=True, text=True, shell=True)
        print("MYPY STDOUT:\n", res.stdout)
        print("MYPY STDERR:\n", res.stderr)
    except Exception as e:
        print("MYPY ERR:", e)

if __name__ == "__main__":
    main()
