import re
from pathlib import Path

env_types = ["DEF", "PROP", "THEO", "LEM", "KORO", "REM", "EXA", "STUD", "CONC"]

env_pattern = re.compile(
    r"\\begin\{(" + "|".join(env_types) + r")\}\{([^\}]+)\}\{([^\}]+)\}(.*?)\\end{\1}",
    re.DOTALL
)

base_dir = Path(__file__).resolve().parent
module_dir = base_dir / "Module"
module_dir.mkdir(exist_ok=True)

for script_path in base_dir.glob("*/**/*_script.tex"):
    script_id = script_path.parent.name
    text = script_path.read_text(encoding="utf-8")

    for match in env_pattern.finditer(text):
        env_type, local_id, env_title, content = match.groups()
        global_id = f"{script_id}_{env_type.lower()}_{local_id.replace('.', '_')}.tex"
        output_path = module_dir / global_id

        full_tex = (
            f"\\begin{{{env_type}}}{{{script_id}.{local_id}}}{{{env_title}}}\n"
            f"{content.strip()}\n"
            f"\\end{{{env_type}}}\n"
        )
        output_path.write_text(full_tex, encoding="utf-8")
        print(f"✓ {output_path.name} gespeichert.")
