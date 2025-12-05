$env:NUITKA_CACHE_DIR = "nuitka_cache"

Write-Host "Starting optimized build for UWBReader..." -ForegroundColor Cyan

python -m nuitka `
    --standalone `
    --onefile `
    --windows-console-mode=disable `
    --enable-plugin=pyqt6 `
    --include-qt-plugins=sensible,styles `
    --windows-icon-from-ico=UWBReader.ico `
    --include-data-file=UWBReader.ico=UWBReader.ico `
    --include-data-file=logo.png=logo.png `
    --output-dir=output `
    --output-filename=UWBReader `
    --assume-yes-for-downloads `
    --jobs=8 `
    --python-flag=-OO `
    --nofollow-import-to=numpy,scipy,pandas,PySide6,matplotlib `
    qt_main.py

if ($LASTEXITCODE -eq 0) {
    Write-Host "Build completed successfully!" -ForegroundColor Green
    Write-Host "Check output in: output" -ForegroundColor Cyan
} else {
    Write-Host "Build failed!" -ForegroundColor Red
}

