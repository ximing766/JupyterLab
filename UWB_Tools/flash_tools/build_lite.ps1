$env:NUITKA_CACHE_DIR = "nuitka_cache"

Write-Host "Starting optimized build for OTA_Flash_Tool..." -ForegroundColor Cyan

python -m nuitka `
    --standalone `
    --onefile `
    --windows-console-mode=disable `
    --enable-plugin=pyqt6 `
    --include-qt-plugins=sensible,styles `
    --windows-icon-from-ico=DK6.ico `
    --include-data-file=DK6.ico=DK6.ico `
    --include-data-file=styles.qss=styles.qss `
    --output-dir=output `
    --output-filename=OTA_Flash_Tool `
    --assume-yes-for-downloads `
    --jobs=8 `
    --python-flag=-OO `
    --nofollow-import-to=numpy,scipy,pandas,matplotlib,IPython,PIL,tkinter `
    OTA_Flash_Tool.py

if ($LASTEXITCODE -eq 0) {
    Write-Host "Build completed successfully!" -ForegroundColor Green
    Write-Host "Check output in: output/OTA_Flash_Tool.exe" -ForegroundColor Cyan
} else {
    Write-Host "Build failed!" -ForegroundColor Red
}
