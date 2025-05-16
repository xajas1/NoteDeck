from pathlib import Path

for path in Path(".").rglob("*.tex"):
    print(path)
