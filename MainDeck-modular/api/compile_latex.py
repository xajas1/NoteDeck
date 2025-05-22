
# Users/tim/NoteDeck/MainDeck-modular/api/compile_latex.py

from fastapi import APIRouter, Request
from fastapi.responses import FileResponse
from tempfile import NamedTemporaryFile
import subprocess
from pathlib import Path
import shutil

router = APIRouter()

@router.post("/compile")
async def compile_tex(request: Request):
    data = await request.json()
    tex_code = data.get("tex", "")
    
    tmp_dir = Path("/tmp/tex_compile")
    tmp_dir.mkdir(parents=True, exist_ok=True)

    tex_file = tmp_dir / "temp.tex"
    tex_file.write_text(tex_code, encoding="utf-8")

    try:
        subprocess.run(
            ["pdflatex", "-interaction=nonstopmode", tex_file.name],
            cwd=tmp_dir,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
    except subprocess.CalledProcessError as e:
        return {"error": "LaTeX compilation failed", "details": e.stderr.decode()}

    pdf_file = tex_file.with_suffix(".pdf")
    if not pdf_file.exists():
        return {"error": "PDF was not generated."}

    return FileResponse(str(pdf_file), media_type="application/pdf")
