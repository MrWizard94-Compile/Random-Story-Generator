"""
run.py — reliable Python execution helper for the Story Generator project.
Called by runpy.bat. Writes stdout+stderr to _run_out.txt.
"""
import sys, os, subprocess, traceback

PROJ = os.path.dirname(os.path.abspath(__file__))
OUT  = os.path.join(PROJ, "_run_out.txt")
PY   = sys.executable

def run_file(path: str) -> str:
    full = path if os.path.isabs(path) else os.path.join(PROJ, path)
    result = subprocess.run(
        [PY, full],
        capture_output=True, text=True,
        encoding="utf-8", errors="replace",
        cwd=PROJ
    )
    return (result.stdout or "") + (result.stderr or "")

def run_code(code: str) -> str:
    import io
    from contextlib import redirect_stdout, redirect_stderr
    buf = io.StringIO()
    try:
        with redirect_stdout(buf), redirect_stderr(buf):
            exec(compile(code, "<run>", "exec"), {"PROJ": PROJ, "__file__": __file__})
    except Exception:
        buf.write(traceback.format_exc())
    return buf.getvalue()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        output = "Usage: run.py -f <script.py>  OR  run.py <inline_code>\n"
    elif sys.argv[1] == "-f" and len(sys.argv) >= 3:
        output = run_file(sys.argv[2])
    else:
        output = run_code(" ".join(sys.argv[1:]))

    # Write to file AND stdout so bat/PowerShell both see it
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(output)
    sys.stdout.write(output)
    sys.stdout.flush()
