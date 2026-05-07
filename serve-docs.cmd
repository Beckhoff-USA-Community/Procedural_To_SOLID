@echo off
REM Local docs server — sets up venv on first run, serves the docs site.
REM
REM Usage:
REM   serve-docs.cmd               serves at http://localhost:8000
REM   serve-docs.cmd build         one-shot static build to .\site\
REM
REM Requirements: Python 3.9+ in PATH.

setlocal
cd /d "%~dp0"
set "VENV=.venv-docs"

if not exist "%VENV%" (
    echo Creating Python venv at %VENV%
    python -m venv "%VENV%"
    if errorlevel 1 goto :err
)

echo Installing/updating MkDocs and plugins
"%VENV%\Scripts\python" -m pip install --quiet --upgrade pip
"%VENV%\Scripts\pip" install --quiet -r requirements-docs.txt
if errorlevel 1 goto :err

if /I "%~1"=="build" (
    echo Building static site to .\site\
    "%VENV%\Scripts\mkdocs" build --strict
    goto :eof
)

echo Starting local server
echo   open http://localhost:8000 ^(Ctrl-C to stop^)
"%VENV%\Scripts\mkdocs" serve %*
goto :eof

:err
echo.
echo Setup failed. Make sure Python 3.9+ is installed and on PATH.
exit /b 1
