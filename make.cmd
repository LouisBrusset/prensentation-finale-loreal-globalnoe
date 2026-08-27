@echo off
REM ============================================================================
REM  Lanceur universel Windows : delegue a make.ps1.
REM
REM  Marche depuis cmd.exe, PowerShell, l'Explorateur ET Git Bash :
REM     make.cmd install          (cmd.exe)
REM     .\make.cmd install        (PowerShell)
REM     ./make.cmd install        (Git Bash)
REM
REM  Memes cibles que make.ps1, make.sh et le Makefile.
REM ============================================================================

setlocal
set "TARGET=%~1"
if "%TARGET%"=="" set "TARGET=help"

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0make.ps1" %TARGET%
exit /b %ERRORLEVEL%
