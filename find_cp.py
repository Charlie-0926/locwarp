import os

def search_files(directory):
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith((".ts", ".tsx")):
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        if "<ControlPanel" in f.read():
                            print(filepath)
                except:
                    pass

search_files(r"c:\Users\Charlie\Downloads\locwarp-main\frontend\src")
