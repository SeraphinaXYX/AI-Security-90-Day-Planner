# AI Security 90-Day Planner - Launcher
$ProjectDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$pythonExe = Join-Path $ProjectDir ".venv\Scripts\python.exe"
$mainPy = Join-Path $ProjectDir "main.py"

if (-not (Test-Path $pythonExe)) {
    Write-Host "Virtual environment not found. Run setup.ps1 first." -ForegroundColor Red
    Start-Process powershell -ArgumentList "-ExecutionPolicy Bypass -File `"$(Join-Path $ProjectDir 'setup.ps1')`""
    exit
}

Set-Location $ProjectDir
& $pythonExe $mainPy
