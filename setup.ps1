# AI Security 90-Day Planner - Setup Script
# Run this once: Right-click > Run with PowerShell

$ErrorActionPreference = "Stop"
$ProjectDir = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host "========================================" -ForegroundColor Cyan
Write-Host " AI Security 90-Day Planner - Setup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check Python
Write-Host "[1/5] Checking Python installation..." -ForegroundColor Yellow
$pythonCmd = $null
foreach ($cmd in @("python", "python3", "py")) {
    try {
        $ver = & $cmd --version 2>&1
        if ($ver -match "Python 3\.(\d+)") {
            $minor = [int]$Matches[1]
            if ($minor -ge 9) {
                $pythonCmd = $cmd
                Write-Host "  Found: $ver" -ForegroundColor Green
                break
            }
        }
    } catch {}
}

if (-not $pythonCmd) {
    Write-Host "  Python 3.9+ not found!" -ForegroundColor Red
    Write-Host ""
    Write-Host "  Please install Python from https://www.python.org/downloads/" -ForegroundColor Yellow
    Write-Host "  IMPORTANT: Check 'Add Python to PATH' during installation!" -ForegroundColor Yellow
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}

# Create virtual environment
Write-Host "[2/5] Creating virtual environment..." -ForegroundColor Yellow
$venvDir = Join-Path $ProjectDir ".venv"
if (-not (Test-Path $venvDir)) {
    & $pythonCmd -m venv $venvDir
    Write-Host "  Created .venv" -ForegroundColor Green
} else {
    Write-Host "  .venv already exists" -ForegroundColor Green
}

# Activate and install dependencies
Write-Host "[3/5] Installing dependencies..." -ForegroundColor Yellow
$pipPath = Join-Path $venvDir "Scripts\pip.exe"
$pythonVenv = Join-Path $venvDir "Scripts\python.exe"

& $pipPath install --upgrade pip -q 2>&1 | Out-Null
& $pipPath install -r (Join-Path $ProjectDir "requirements.txt") 2>&1 | ForEach-Object {
    if ($_ -match "Successfully installed") {
        Write-Host "  $_" -ForegroundColor Green
    }
}
Write-Host "  Dependencies installed" -ForegroundColor Green

# Create data directory
Write-Host "[4/5] Creating data directory..." -ForegroundColor Yellow
$dataDir = Join-Path $ProjectDir "data"
if (-not (Test-Path $dataDir)) {
    New-Item -ItemType Directory -Path $dataDir | Out-Null
    New-Item -ItemType Directory -Path (Join-Path $dataDir "backups") | Out-Null
}
Write-Host "  Data directory ready" -ForegroundColor Green

# Create desktop shortcut
Write-Host "[5/5] Creating desktop shortcut..." -ForegroundColor Yellow
$desktopPath = [Environment]::GetFolderPath("Desktop")
$shortcutPath = Join-Path $desktopPath "AI Security Planner.lnk"
$launchScript = Join-Path $ProjectDir "launch.ps1"

$WScriptShell = New-Object -ComObject WScript.Shell
$shortcut = $WScriptShell.CreateShortcut($shortcutPath)
$shortcut.TargetPath = "powershell.exe"
$shortcut.Arguments = "-ExecutionPolicy Bypass -WindowStyle Hidden -File `"$launchScript`""
$shortcut.WorkingDirectory = $ProjectDir
$shortcut.Description = "AI Security 90-Day Planner"
$shortcut.Save()
Write-Host "  Desktop shortcut created" -ForegroundColor Green

# Ask about Windows startup
Write-Host ""
$startup = Read-Host "Enable auto-start on Windows login? (y/n)"
if ($startup -eq "y" -or $startup -eq "Y") {
    $startupDir = [Environment]::GetFolderPath("Startup")
    $startupShortcut = Join-Path $startupDir "AI Security Planner.lnk"
    $shortcut2 = $WScriptShell.CreateShortcut($startupShortcut)
    $shortcut2.TargetPath = "powershell.exe"
    $shortcut2.Arguments = "-ExecutionPolicy Bypass -WindowStyle Hidden -File `"$launchScript`""
    $shortcut2.WorkingDirectory = $ProjectDir
    $shortcut2.Description = "AI Security 90-Day Planner"
    $shortcut2.Save()
    Write-Host "  Startup shortcut created" -ForegroundColor Green
} else {
    Write-Host "  Skipped (you can enable this later in Settings)" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host " Setup Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "To launch: double-click 'AI Security Planner' on your Desktop" -ForegroundColor White
Write-Host "Or run: .\launch.ps1" -ForegroundColor White
Write-Host ""

# Launch now?
$launch = Read-Host "Launch the application now? (y/n)"
if ($launch -eq "y" -or $launch -eq "Y") {
    & $pythonVenv (Join-Path $ProjectDir "main.py")
}
