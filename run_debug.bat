@echo off
cd /d "%~dp0"
python debug_run.py > output.txt 2>&1
echo Done. Check output.txt