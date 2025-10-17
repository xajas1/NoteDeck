from pathlib import Path

module_dir = Path("Module")
tex_files = sorted([f.stem for f in module_dir.glob("*.tex")])

dropdown = ",".join(tex_files)
snippet = f'\\input{{../Module/${{1|{dropdown}|}}}}'

print("\n📦 Snippet für VS Code:\n")
print(snippet)
