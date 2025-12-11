$env:NUITKA_CACHE_DIR = "nuitka_cache"

Write-Host "Starting optimized build for UwbBuildTool..." -ForegroundColor Cyan

python -m nuitka `
    --standalone `
    --windows-console-mode=disable `
    --enable-plugin=pyqt6 `
    --include-qt-plugins=sensible,styles `
    --windows-icon-from-ico=compile_tool.ico `
    --include-data-file=compile_tool.ico=compile_tool.ico `
    --include-data-file=styles.qss=styles.qss `
    --include-data-file=config.json=config.json `
    --output-dir=output `
    --output-filename=UwbBuildTool `
    --assume-yes-for-downloads `
    --jobs=8 `
    --python-flag=-OO `
    --nofollow-import-to=numpy,scipy,pandas,matplotlib,IPython,PIL `
    main.py

if ($LASTEXITCODE -eq 0) {
    Write-Host "Build completed successfully!" -ForegroundColor Green
    Write-Host "Check output in: output/UwbBuildTool.exe" -ForegroundColor Cyan
} else {
    Write-Host "Build failed!" -ForegroundColor Red
}
