# 生成ai模块exe
$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Resolve-Path (Join-Path $scriptDir "..\..")
$pyinstaller = Join-Path $projectRoot ".venv\Scripts\pyinstaller.exe"
$backendEntry = Join-Path $projectRoot "src\ai-module\backend.py"
$resultSource = Join-Path $projectRoot "result"
$distResult = Join-Path $projectRoot "dist\result"
$exePath = Join-Path $projectRoot "dist\ai-module-backend\ai-module-backend.exe"

if (-not (Test-Path $pyinstaller)) {
    throw "PyInstaller not found: $pyinstaller"
}

Set-Location $projectRoot

Remove-Item -Recurse -Force "build", "dist", "ai-module-backend.spec" -ErrorAction SilentlyContinue

& $pyinstaller --noconfirm --clean --onedir --console `
    --name ai-module-backend `
    --paths "src\ai-module" `
    --add-data "src\ai-module;." `
    --collect-all pypandoc `
    --collect-all docx `
    --hidden-import pythoncom `
    --hidden-import pywintypes `
    --hidden-import win32com `
    --hidden-import win32com.client `
    $backendEntry

if (Test-Path $resultSource) {
    Copy-Item -Recurse -Force $resultSource $distResult
}

Write-Host "Pack complete."
Write-Host "Run: $exePath"
