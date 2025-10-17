# src/cli.py
import click
from pathlib import Path

# WICHTIG: relative Imports, damit `python -m src.cli` funktioniert
from .llm.critique import critique_sheet
from .llm.refine import refine_sheet
from .build_tex import build_full_tex

@click.group(help="CLI für die Aufgaben-Pipeline (solve/review/refine/build).")
def cli():
    pass

@cli.command("improve_once")
@click.argument("ex_json")
@click.argument("version")  # z. B. v1 oder v2
def improve_once_cmd(ex_json, version):
    """
    Eine Iteration ausführen, OHNE etwas zu überschreiben:
      - Review (critique) für <version>
      - Refine -> neue Version (v{+1})
      - Build Full .tex mit Präambel (solutions_v{+1}_full.tex)
    """
    base = Path(ex_json).parent
    sol_dir = base / "solutions" / version
    rev_dir = base / "reviews" / version
    next_v = f"v{int(version.replace('v',''))+1}"

    rev_dir.mkdir(parents=True, exist_ok=True)

    # 1) Review: schreibt JSONs nach reviews/<version>/
    critique_sheet(ex_json, str(sol_dir), str(rev_dir))

    # 2) Refine: erzeugt neue Lösungen in solutions/<next_v>/
    refine_sheet(ex_json, str(sol_dir), str(rev_dir), str(base / "solutions" / next_v))

    # 3) Build: erzeugt zusammengefasste TeX (mit Präambel), inkl. [vX]-Labels
    build_full_tex(ex_json, next_v, None, f"Lösungen ({next_v})")

    click.echo(f"✔ Iteration abgeschlossen → neue Version: {next_v}")

if __name__ == "__main__":
    cli()
