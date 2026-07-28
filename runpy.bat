@echo off
:: runpy.bat — runs a Python script via the venv and captures output reliably
:: Usage: runpy script.py
:: Output always lands in _run_out.txt AND prints to console

set PROJ=%~dp0
set PY=%PROJ%.venv\Scripts\python.exe
set OUT=%PROJ%_run_out.txt

"%PY%" "%PROJ%run.py" -f %1 > "%OUT%" 2>&1
type "%OUT%"
