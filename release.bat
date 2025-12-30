@echo off
setlocal

REM Extract version from _version.py
for /f "tokens=2 delims==" %%I in ('findstr "__version__" _version.py') do set VERSION=%%~I
REM Remove leading space if any (simple way)
set VERSION=%VERSION: =%
REM Remove quotes
set VERSION=%VERSION:"=%

if "%VERSION%"=="" (
    echo Error: Could not extract version from _version.py
    exit /b 1
)

echo Detected version: %VERSION%

REM Update pyproject.toml using PowerShell for better regex support
powershell -Command "(Get-Content pyproject.toml) -replace 'version = \".*\"', 'version = \"%VERSION%\"' | Set-Content pyproject.toml"

git add .
git commit -m "Release v%VERSION%"
if %errorlevel% neq 0 (
    echo Warning: Commit failed or nothing to commit. Continuing...
)

git push origin main

git tag "v%VERSION%"
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Tag v%VERSION% already exists!
    echo Please update the version in _version.py before releasing.
    echo The script will stop here to prevent triggering CI with old code.
    exit /b 1
)

git push origin "v%VERSION%"

echo Released v%VERSION%
