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

echo 📋 Task: %TASK%
echo.

echo 🔄 Connecting to GitHub...
git clone https://github.com/%REPO%.git temp_gamma 2>nul
if %errorlevel% neq 0 (
    echo 📁 Repo exists, pulling latest...
    cd temp_gamma
    git pull
    goto :continue
)

:continue
cd temp_gamma

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