import sys

def check_braces(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        content = f.read()
    
    stack = []
    for i, char in enumerate(content):
        if char in '{[(':
            stack.append((char, i))
        elif char in '}])':
            if not stack:
                print(f"Extra closing {char} at {i}")
                return
            top, _ = stack.pop()
            if (top == '{' and char != '}') or \
               (top == '[' and char != ']') or \
               (top == '(' and char != ')'):
                print(f"Mismatch: {top} and {char} at {i}")
                return
    if stack:
        print(f"Unclosed: {stack}")
    else:
        print("Braces OK")

check_braces(r"c:\Users\Charlie\Downloads\locwarp-main\frontend\src\hooks\useSimulation.ts")
check_braces(r"c:\Users\Charlie\Downloads\locwarp-main\frontend\src\components\ControlPanel.tsx")
check_braces(r"c:\Users\Charlie\Downloads\locwarp-main\frontend\src\App.tsx")
check_braces(r"c:\Users\Charlie\Downloads\locwarp-main\frontend\src\services\api.ts")
