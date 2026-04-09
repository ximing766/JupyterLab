$env:NUITKA_CACHE_DIR = "nuitka_cache"

Write-Host "Starting optimized build for UWBDash..." -ForegroundColor Cyan

# 1. Clean previous build artifacts if needed (optional)
# if (Test-Path "../../output/UWBDash.dist") { Remove-Item "../../output/UWBDash.dist" -Recurse -Force }
# if (Test-Path "../../output/UWBDash.build") { Remove-Item "../../output/UWBDash.build" -Recurse -Force }

# 2. Run Nuitka with optimization flags
# Key changes for size reduction:
# - Replaced --nofollow-import-to with --no-include-package for heavy libraries
#   (This prevents them from being copied to the dist folder entirely)
# - Explicitly excluded numpy, scipy, pandas, matplotlib, PySide6

python -m nuitka `
    --standalone `
    --windows-console-mode=disable `
    --enable-plugin=pyqt6 `
    --windows-icon-from-ico=./logo.ico `
    --include-data-dir=./pic=./pic `
    --include-data-file=./config.json=./config.json `
    --include-data-file=./config/viki.pl=./config/viki.pl `
    --include-data-file=./UWBDash.json=./UWBDash.json `
    --include-data-file=./logo.ico=./logo.ico `
    --include-module=log `
    --include-module=position_view `
    --include-module=splash_screen `
    --include-module=user_manager `
    --output-dir=../../output `
    --jobs=8 `
    --python-flag=-OO `
    --nofollow-import-to=numpy `
    --nofollow-import-to=scipy `
    --nofollow-import-to=pandas `
    --nofollow-import-to=matplotlib `
    --nofollow-import-to=PySide6 `
    --product-name="UWBDash" `
    --product-version="2.3.1" `
    --file-version="1.0.0.0" `
    --copyright="CardShare@Qilang² © 2025" `
    --trademarks="UWBDash" `
    UWBDash.py

if ($LASTEXITCODE -eq 0) {
    Write-Host "Build completed successfully!" -ForegroundColor Green
    Write-Host "Check output in: ../../output/UWBDash.dist" -ForegroundColor Cyan
} else {
    Write-Host "Build failed!" -ForegroundColor Red
}
