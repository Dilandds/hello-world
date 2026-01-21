# Build script for Windows EXE distribution
# Creates standalone .exe file using PyInstaller

$ErrorActionPreference = "Stop"  # Exit on error

Write-Host "Building STL 3D Viewer for Windows..." -ForegroundColor Cyan

# Get script directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

# Check if PyInstaller is installed
try {
    $null = Get-Command pyinstaller -ErrorAction Stop
    Write-Host "✓ PyInstaller found" -ForegroundColor Green
} catch {
    Write-Host "PyInstaller not found. Installing..." -ForegroundColor Yellow
    pip install pyinstaller>=6.0.0
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Error: Failed to install PyInstaller" -ForegroundColor Red
        exit 1
    }
}

# Clean previous builds
Write-Host "Cleaning previous builds..." -ForegroundColor Yellow
if (Test-Path "build") {
    Remove-Item -Recurse -Force "build"
}
if (Test-Path "dist") {
    Remove-Item -Recurse -Force "dist"
}

# Build with PyInstaller
Write-Host "Running PyInstaller..." -ForegroundColor Cyan
pyinstaller stl_viewer_windows.spec --clean --noconfirm

if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: PyInstaller build failed" -ForegroundColor Red
    exit 1
}

# Check if EXE was created
$ExePath = "dist\STL 3D Viewer.exe"
if (-not (Test-Path $ExePath)) {
    Write-Host "Error: EXE not found at $ExePath" -ForegroundColor Red
    exit 1
}

Write-Host "✓ EXE created successfully: $ExePath" -ForegroundColor Green

# Get file size
$FileInfo = Get-Item $ExePath
$SizeMB = [math]::Round($FileInfo.Length / 1MB, 2)
Write-Host "  Size: $SizeMB MB" -ForegroundColor Cyan

Write-Host ""
Write-Host "Build complete! File:" -ForegroundColor Green
Write-Host "  - EXE: $ExePath" -ForegroundColor White
