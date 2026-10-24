@echo off
cd /d "%~dp0"

if exist ".venv\Scripts\pythonw.exe" (
    start "" ".venv\Scripts\pythonw.exe" "%~dp0main.py"
    exit /b
)
if exist "%LocalAppData%\Programs\Python\Python312\pythonw.exe" (
    start "" "%LocalAppData%\Programs\Python\Python312\pythonw.exe" "%~dp0main.py"
    exit /b
)
where pythonw >nul 2>nul
if %errorlevel% equ 0 (
    start "" pythonw "%~dp0main.py"
    exit /b
)
python "%~dp0main.py"
