import os

def search_text(directory, target):
    found = []
    for root, dirs, files in os.walk(directory):
        if 'venv' in root or '.git' in root or '.gemini' in root:
            continue
        for file in files:
            path = os.path.join(root, file)
            try:
                with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    if target.lower() in content.lower():
                        found.append(path)
            except Exception:
                pass
    return found

print("Search for 'pelotao':", search_text('.', 'pelotao'))
print("Search for 'balm':", search_text('.', 'balm'))
print("Search for 'tarantino':", search_text('.', 'tarantino'))
