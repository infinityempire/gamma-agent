@echo off
:: Gamma Agent - Send Command Script (Windows)
:: Usage: send_command.bat "Your question here"

setlocal

set REPO=infinityempire/gamma-agent
set BRANCH=master
set COMMANDS_DIR=commands
set COMMAND_FILE=command_%RANDOM%.txt

color 0A

echo.
echo  ╔══════════════════════════════════════════════════════════════╗
echo  ║              GAMMA AGENT - COMMAND SENDER                  ║
echo  ╚══════════════════════════════════════════════════════════════╝
echo.

:: Check if task is provided
if "%~1"=="" (
    echo ❌ Error: No task provided!
    echo.
    echo Usage: send_command.bat "Your question here"
    echo.
    echo Example: send_command.bat "Who are the prime ministers of Israel?"
    exit /b 1
)

set TASK=%~1

:: Check for GH_TOKEN
if "%GH_TOKEN%"=="" (
    echo.
    echo Error: GH_TOKEN environment variable is not set!
    echo.
    echo Please set it before running:
    echo   set GH_TOKEN=your_token_here
    exit /b 1
)

echo Task: %TASK%
echo.

echo Connecting to GitHub...
set CLONE_URL=https://x-access-token:%GH_TOKEN%@github.com/%REPO%.git
if exist temp_gamma rmdir /s /q temp_gamma
git clone "%CLONE_URL%" temp_gamma
if %errorlevel% neq 0 (
    echo.
    echo Error: Failed to clone repository. Check your GH_TOKEN.
    exit /b 1
)

:continue
cd temp_gamma
git config user.email "gamma-agent[bot]@users.noreply.github.com"
git config user.name "Gamma Agent"
git remote set-url origin "%CLONE_URL%"

:: Create commands folder if not exists
if not exist %COMMANDS_DIR% mkdir %COMMANDS_DIR%

:: Create command file
echo %TASK% > %COMMANDS_DIR%\%COMMAND_FILE%

echo ✅ Command file created: %COMMANDS_DIR%\%COMMAND_FILE%
echo 📤 Pushing to GitHub...

:: Commit and push
git add %COMMANDS_DIR%\
git commit -m "🤖 New command: %TASK%"
git push origin %BRANCH%

if %errorlevel% neq 0 (
    echo.
    echo ❌ Error: Failed to push to GitHub!
    echo Make sure you have git credentials configured.
    cd ..
    rmdir /s /q temp_gamma 2>nul
    exit /b 1
)

echo.
echo ✅ Command sent successfully!
echo.
echo ⏳ Gamma Agent will pick it up automatically...
echo.
echo 📊 Check progress at:
echo    https://github.com/%REPO%/actions
echo.
echo 📁 Commands will be archived in:
echo    https://github.com/%REPO%/tree/master/archive
echo.

:: Cleanup
cd ..
rmdir /s /q temp_gamma 2>nul

pause