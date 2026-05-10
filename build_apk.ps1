# build_apk.ps1 — Builds the Android APK using Docker + Buildozer.
# Run from the project directory:  .\build_apk.ps1
# First build downloads ~4 GB (Android SDK/NDK) and takes 30–60 min.
# Subsequent builds use the cached .buildozer volume and take ~5 min.

$ProjectDir  = $PSScriptRoot
$ImageName   = "doodle-loot-builder"
$CacheVolume = "doodle_loot_buildozer_cache"

# ── 1. Ensure Docker is running ───────────────────────────────────────────────
Write-Host "Checking Docker..." -ForegroundColor Cyan
$dockerInfo = docker info 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "Docker is not running. Starting Docker Desktop..." -ForegroundColor Yellow
    Start-Process "C:\Program Files\Docker\Docker\Docker Desktop.exe"
    Write-Host "Waiting 30 seconds for Docker to start..."
    Start-Sleep -Seconds 30
    $dockerInfo = docker info 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Docker still not available. Open Docker Desktop manually and re-run." -ForegroundColor Red
        exit 1
    }
}
Write-Host "Docker is running." -ForegroundColor Green

# ── 2. Build the builder image (only rebuilds if Dockerfile changed) ──────────
Write-Host "`nBuilding builder image '$ImageName'..." -ForegroundColor Cyan
docker build -f "$ProjectDir\Dockerfile.build" -t $ImageName "$ProjectDir"
if ($LASTEXITCODE -ne 0) { Write-Host "Image build failed." -ForegroundColor Red; exit 1 }

# ── 3. Create a named volume for SDK/NDK cache ────────────────────────────────
docker volume create $CacheVolume | Out-Null
Write-Host "Using cache volume: $CacheVolume" -ForegroundColor Cyan

# ── 4. Run Buildozer inside Docker ────────────────────────────────────────────
Write-Host "`nStarting APK build (first run downloads Android SDK — be patient)..." -ForegroundColor Yellow
Write-Host "Logs will stream below.`n"

# Mount project dir as /app and the persistent cache as ~/.buildozer
docker run --rm `
    -v "${ProjectDir}:/app" `
    -v "${CacheVolume}:/root/.buildozer" `
    $ImageName

$exitCode = $LASTEXITCODE

# ── 5. Report result ──────────────────────────────────────────────────────────
if ($exitCode -eq 0) {
    $apk = Get-ChildItem "$ProjectDir\bin\*.apk" -ErrorAction SilentlyContinue | Select-Object -Last 1
    if ($apk) {
        Write-Host "`nBuild successful!" -ForegroundColor Green
        Write-Host "APK: $($apk.FullName)" -ForegroundColor Green

        # Copy to Desktop for easy access
        $dest = "$env:USERPROFILE\Desktop\DoodleLoot.apk"
        Copy-Item $apk.FullName $dest -Force
        Write-Host "Copied to Desktop: $dest" -ForegroundColor Green
        Write-Host "`nInstall on phone:"
        Write-Host "  adb install `"$dest`""
        Write-Host "  (or transfer the file manually and tap it on Android)"
    } else {
        Write-Host "`nBuild finished but no APK found in bin\. Check logs above." -ForegroundColor Yellow
    }
} else {
    Write-Host "`nBuild FAILED (exit $exitCode). Scroll up for the error." -ForegroundColor Red
    Write-Host "Tip: check .buildozer/android/platform/build-*/dists/*/build.log"
}
