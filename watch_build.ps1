# watch_build.ps1 - Live build progress monitor.
# Run in a separate terminal while build_apk.ps1 is running.

param([string]$LogFile = "")

if (-not $LogFile) {
    $taskDir = "$env:LOCALAPPDATA\Temp\claude"
    $LogFile = Get-ChildItem "$taskDir\*\*\tasks\*.output" -Recurse -ErrorAction SilentlyContinue |
               Sort-Object LastWriteTime -Descending |
               Select-Object -First 1 -ExpandProperty FullName
    if (-not $LogFile) {
        Write-Host "No active build log found. Start build_apk.ps1 first." -ForegroundColor Red
        exit 1
    }
}

$stages = @(
    @{ Name = "Download Android SDK/tools";  Pattern = "Android SDK is missing" },
    @{ Name = "Download Android NDK";        Pattern = "Android NDK is missing" },
    @{ Name = "Download recipe sources";     Pattern = "Downloading pygame" },
    @{ Name = "Unpack recipes";              Pattern = "Unpacking hostpython3" },
    @{ Name = "Build host Python";           Pattern = "Building hostpython3" },
    @{ Name = "Configure OpenSSL";           Pattern = "checking for utimes" },
    @{ Name = "Compile OpenSSL";             Pattern = "crypto/cms/cms_env" },
    @{ Name = "Configure Python 3.11 ARM";   Pattern = "checking for wait4" },
    @{ Name = "Compile Python 3.11 ARM";     Pattern = "Building python3 for armeabi" },
    @{ Name = "Compile Python 3.11 ARM64";   Pattern = "Building python3 for arm64" },
    @{ Name = "Build SDL2";                  Pattern = "Building sdl2" },
    @{ Name = "Build pygame";               Pattern = "Building pygame" },
    @{ Name = "Package and sign APK";        Pattern = "Packaging the application" },
    @{ Name = "Done!";                       Pattern = "APK available" }
)

function Draw-Bar([int]$cur, [int]$total, [int]$width = 40) {
    $filled = [Math]::Round($width * $cur / [Math]::Max(1, $total))
    $bar    = ("=" * $filled).PadRight($width, "-")
    $pct    = [Math]::Round(100 * $cur / [Math]::Max(1, $total))
    return "[" + $bar + "] " + $pct + "%"
}

$spinChars = @("|", "/", "-", "\")
$spin      = 0
$startTime = Get-Date

while ($true) {
    if (-not (Test-Path $LogFile)) {
        Write-Host "Waiting for log file..." -ForegroundColor DarkGray
        Start-Sleep -Seconds 2
        continue
    }

    $content = Get-Content $LogFile -Raw -ErrorAction SilentlyContinue
    if (-not $content) { Start-Sleep -Seconds 2; continue }

    $reached = -1
    for ($i = 0; $i -lt $stages.Count; $i++) {
        if ($content -match $stages[$i].Pattern) { $reached = $i }
    }

    $elapsed    = (Get-Date) - $startTime
    $elapsedStr = "{0:mm\:ss}" -f $elapsed

    Clear-Host
    Write-Host ""
    Write-Host ("  Doodle Loot - APK Build Monitor  [" + $elapsedStr + " elapsed]") -ForegroundColor Cyan
    Write-Host ("  " + $spinChars[$spin % 4] + " " + (Split-Path $LogFile -Leaf)) -ForegroundColor DarkGray
    Write-Host ""

    for ($i = 0; $i -lt $stages.Count; $i++) {
        $name = $stages[$i].Name
        if ($i -lt $reached) {
            Write-Host ("  [OK]  " + $name) -ForegroundColor Green
        } elseif ($i -eq $reached) {
            Write-Host ("  [" + $spinChars[$spin % 4] + "]   " + $name) -ForegroundColor Yellow
        } else {
            Write-Host ("  [ ]   " + $name) -ForegroundColor DarkGray
        }
    }

    Write-Host ""
    $bar = Draw-Bar -cur ([Math]::Max(0, $reached)) -total ($stages.Count - 1)
    Write-Host ("  " + $bar + "  stage " + ([Math]::Max(0,$reached+1)) + "/" + $stages.Count) -ForegroundColor Cyan

    $failed = ($content -match "BUILD FAILED") -or ($content -match "Traceback.most recent") -or ($content -match "Recipe build failed")
    if ($failed) {
        Write-Host ""
        Write-Host "  BUILD FAILED - check the full log for details." -ForegroundColor Red
        $lines   = $content -split "`n"
        $errLine = $lines | Where-Object { $_ -match "Error:" -or $_ -match "FAILED" } | Select-Object -Last 1
        Write-Host ("  " + $errLine.Trim()) -ForegroundColor Red
        break
    }

    if ($reached -eq ($stages.Count - 1)) {
        Write-Host ""
        Write-Host "  BUILD COMPLETE!" -ForegroundColor Green
        $apk = Get-ChildItem (Join-Path $PSScriptRoot "bin\*.apk") -ErrorAction SilentlyContinue |
               Select-Object -Last 1
        if ($apk) {
            Write-Host ("  APK: " + $apk.FullName) -ForegroundColor Green
        }
        break
    }

    $spin++
    Start-Sleep -Seconds 4
}
