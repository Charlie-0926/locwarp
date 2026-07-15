with open("frontend/src/App.tsx", 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if "SimMode" in line:
        print(f"{i+1}: {line.strip()}")
