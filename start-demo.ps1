param([int]$Port = 8000)
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$pyLauncher = Get-Command py -ErrorAction SilentlyContinue
if ($pyLauncher) {
    & $pyLauncher.Source -3 app.py --port $Port
    exit $LASTEXITCODE
}
$bundledPython = Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
if (Test-Path -LiteralPath $bundledPython) {
    & $bundledPython app.py --port $Port
    exit $LASTEXITCODE
}
$pythonCommand = Get-Command python -ErrorAction SilentlyContinue
if ($pythonCommand -and $pythonCommand.Source -notlike '*\WindowsApps\*') {
    & $pythonCommand.Source app.py --port $Port
    exit $LASTEXITCODE
}
Write-Error 'Python 3.10+ is required. Install Python, then run python app.py.'
