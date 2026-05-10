# Creates a desktop shortcut for the Doodle Loot prototype.
# Run once from the project directory:  .\create_shortcut.ps1

$ProjectDir  = $PSScriptRoot
$CondaRoot   = "C:\ProgramData\miniconda3"   # adjust if miniconda lives elsewhere
$EnvName     = "doodle_loot"
$DesktopPath = [Environment]::GetFolderPath("Desktop")
$ShortcutPath = Join-Path $DesktopPath "Doodle Loot.lnk"

# ── Write a small launcher batch file in the project directory ─────────────────
$LauncherPath = Join-Path $ProjectDir "run_game.bat"
$BatchContent = @"
@echo off
title Doodle Loot
call "$CondaRoot\Scripts\activate.bat" $EnvName
cd /d "$ProjectDir"
python main.py
if %errorlevel% neq 0 (
    echo.
    echo Game exited with error code %errorlevel%
    pause
)
"@
Set-Content -Path $LauncherPath -Value $BatchContent -Encoding ASCII

# ── Create the desktop .lnk shortcut ──────────────────────────────────────────
$Shell    = New-Object -ComObject WScript.Shell
$Shortcut = $Shell.CreateShortcut($ShortcutPath)

$Shortcut.TargetPath       = $LauncherPath
$Shortcut.WorkingDirectory = $ProjectDir
$Shortcut.WindowStyle      = 1          # 1 = normal window
$Shortcut.Description      = "Doodle Loot prototype (pygame)"

# Use the Python interpreter icon from the conda env (fallback to cmd icon)
$PythonExe = "$CondaRoot\envs\$EnvName\python.exe"
if (Test-Path $PythonExe) {
    $Shortcut.IconLocation = "$PythonExe,0"
}

$Shortcut.Save()

Write-Host "Launcher written : $LauncherPath"
Write-Host "Desktop shortcut : $ShortcutPath"
Write-Host ""
Write-Host "Double-click 'Doodle Loot' on your desktop to launch."
