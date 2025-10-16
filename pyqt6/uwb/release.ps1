# UWBDash Release Script
# Author: @Qilang²
# Description: Automated release script for UWBDash application

param(
    [switch]$Force,
    [switch]$SkipConfirm,
    [string]$CustomVersion = ""
)

# Set error action preference
$ErrorActionPreference = "Stop"

# Define colors for output
$Colors = @{
    Success = "Green"
    Warning = "Yellow"
    Error = "Red"
    Info = "Cyan"
    Header = "Magenta"
}

# Function to write colored output
function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Color = "White"
    )
    
    # Set console encoding to UTF-8 for better Unicode support
    [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
    Write-Host $Message -ForegroundColor $Colors[$Color]
}

# Function to extract version from UWBDash.py
function Get-AppVersion {
    $scriptDir = Split-Path -Parent $MyInvocation.ScriptName
    $uwbDashPath = Join-Path $scriptDir "UWBDash.py"
    
    if (-not (Test-Path $uwbDashPath)) {
        throw "UWBDash.py not found at: $uwbDashPath"
    }
    
    $content = Get-Content $uwbDashPath -Raw
    $versionMatch = [regex]::Match($content, 'APP_VERSION\s*=\s*"([^"]*)"')
    
    if ($versionMatch.Success) {
        return $versionMatch.Groups[1].Value
    } else {
        throw "Could not extract version from UWBDash.py"
    }
}

# Function to check if required tools are available
function Test-RequiredTools {
    Write-ColorOutput "Checking required tools..." "Info"
    
    # Check if gh is available
    try {
        $ghVersion = gh --version 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-ColorOutput "[OK] GitHub CLI (gh) is available" "Success"
        } else {
            throw "GitHub CLI not found"
        }
    } catch {
        Write-ColorOutput "[ERROR] GitHub CLI (gh) is not available or not in PATH" "Error"
        Write-ColorOutput "Please install GitHub CLI: https://cli.github.com/" "Warning"
        exit 1
    }
    
    # Check if PowerShell Compress-Archive is available (built-in Windows compression)
    try {
        Get-Command Compress-Archive -ErrorAction Stop | Out-Null
        Write-ColorOutput "[OK] PowerShell Compress-Archive is available" "Success"
    } catch {
        Write-ColorOutput "[ERROR] PowerShell Compress-Archive not available" "Error"
        Write-ColorOutput "Please ensure you're running PowerShell 5.0 or later" "Warning"
        exit 1
    }
}

# Function to clean build directory
function Remove-BuildDirectory {
    param([string]$BuildPath)
    
    Write-ColorOutput "Cleaning build directory..." "Info"
    
    if (Test-Path $BuildPath) {
        try {
            Remove-Item $BuildPath -Recurse -Force
            Write-ColorOutput "[OK] Build directory removed: $BuildPath" "Success"
        } catch {
            Write-ColorOutput "[ERROR] Failed to remove build directory: $_" "Error"
            throw
        }
    } else {
        Write-ColorOutput "ℹ Build directory does not exist: $BuildPath" "Warning"
    }
}

# Function to compress dist directory
function Compress-DistDirectory {
    param(
        [string]$DistPath,
        [string]$OutputPath,
        [string]$Version
    )
    
    Write-ColorOutput "Compressing dist directory..." "Info"
    
    if (-not (Test-Path $DistPath)) {
        throw "Dist directory not found: $DistPath"
    }
    
    # Create output directory if it doesn't exist
    $outputDir = Split-Path $OutputPath -Parent
    if (-not (Test-Path $outputDir)) {
        New-Item -ItemType Directory -Path $outputDir -Force | Out-Null
    }
    
    # Remove existing archive if it exists
    if (Test-Path $OutputPath) {
        Remove-Item $OutputPath -Force
        Write-ColorOutput "Removed existing archive: $OutputPath" "Warning"
    }
    
    try {
        Write-ColorOutput "Creating ZIP archive with PowerShell Compress-Archive..." "Info"
        Write-ColorOutput "Source: $DistPath\*" "Info"
        Write-ColorOutput "Destination: $OutputPath" "Info"
        
        # Use PowerShell's built-in Compress-Archive to create ZIP archive
        Compress-Archive -Path "$DistPath\*" -DestinationPath $OutputPath -CompressionLevel Optimal -Force
        
        if (Test-Path $OutputPath) {
            $archiveSize = (Get-Item $OutputPath).Length / 1MB
            Write-ColorOutput "[OK] Archive created successfully: $OutputPath" "Success"
            Write-ColorOutput "Archive size: $([math]::Round($archiveSize, 2)) MB" "Info"
        } else {
            throw "Archive file was not created"
        }
    } catch {
        Write-ColorOutput "[ERROR] Failed to compress dist directory: $_" "Error"
        throw
    }
}

# Function to create GitHub release
function New-GitHubRelease {
    param(
        [string]$Version,
        [string]$ArchivePath
    )
    
    Write-ColorOutput "Creating GitHub release..." "Info"
    
    if (-not (Test-Path $ArchivePath)) {
        throw "Archive file not found: $ArchivePath"
    }
    
    # Check if we're in a git repository
    try {
        $gitStatus = git status 2>$null
        if ($LASTEXITCODE -ne 0) {
            throw "Not in a git repository"
        }
    } catch {
        Write-ColorOutput "[ERROR] Not in a git repository or git not available" "Error"
        throw
    }
    
    # Check if release already exists
    try {
        $existingRelease = gh release view $Version 2>$null
        if ($LASTEXITCODE -eq 0) {
            if ($Force) {
                Write-ColorOutput "Release $Version already exists. Deleting due to -Force flag..." "Warning"
                gh release delete $Version --yes
            } else {
                Write-ColorOutput "[ERROR] Release $Version already exists. Use -Force to overwrite." "Error"
                return $false
            }
        }
    } catch {
        # Release doesn't exist, which is what we want
    }
    
    try {
        # Create release notes
        $releaseNotes = @"
# UWBDash $Version Release

## Updates in this version
- Bug fixes and performance improvements
- Updated dependencies
- Enhanced user interface

---
**Build Date**: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')
**Author**: @ximing766
"@
        
        # Create the release
        Write-ColorOutput "Creating release $Version..." "Info"
        gh release create $Version `
            --title "UWBDash $Version" `
            --notes $releaseNotes `
            --latest
        
        if ($LASTEXITCODE -eq 0) {
            Write-ColorOutput "[OK] GitHub release created successfully" "Success"
            
            # Upload the archive
            Write-ColorOutput "Uploading archive to release..." "Info"
            gh release upload $Version $ArchivePath
            
            if ($LASTEXITCODE -eq 0) {
                Write-ColorOutput "[OK] Archive uploaded successfully" "Success"
                
                # Get release URL
                $releaseUrl = gh release view $Version --json url --jq .url
                Write-ColorOutput "Release URL: $releaseUrl" "Header"
                return $true
            } else {
                Write-ColorOutput "[ERROR] Failed to upload archive" "Error"
                return $false
            }
        } else {
            Write-ColorOutput "[ERROR] Failed to create GitHub release" "Error"
            return $false
        }
    } catch {
        Write-ColorOutput "[ERROR] Error creating GitHub release: $_" "Error"
        return $false
    }
}

# Main execution
try {
    Write-ColorOutput "UWBDash Release Script Started" "Header"
    Write-ColorOutput "======================================" "Header"
    
    # Get version
    if ($CustomVersion) {
        $version = $CustomVersion
        Write-ColorOutput "Using custom version: $version" "Info"
    } else {
        $version = Get-AppVersion
        Write-ColorOutput "Detected version from UWBDash.py: $version" "Info"
    }
    
    # Define paths
    $rootPath = "e:\Work\Python\JupyterLab"
    $buildPath = Join-Path $rootPath "output\UWBDash.build"
    $distPath = Join-Path $rootPath "output\UWBDash.dist"
    $archivePath = Join-Path $rootPath "output\UWBDash.zip"
    
    Write-ColorOutput "Build path: $buildPath" "Info"
    Write-ColorOutput "Dist path: $distPath" "Info"
    Write-ColorOutput "Archive path: $archivePath" "Info"
    
    # Check required tools
    Test-RequiredTools
    
    # Confirmation prompt
    if (-not $SkipConfirm) {
        Write-ColorOutput "`nRelease Summary:" "Header"
        Write-ColorOutput "- Version: $version" "Info"
        Write-ColorOutput "- Build directory will be deleted: $buildPath" "Warning"
        Write-ColorOutput "- Dist directory will be compressed: $distPath" "Info"
        Write-ColorOutput "- Archive will be created: $archivePath" "Info"
        Write-ColorOutput "- GitHub release will be created with archive" "Info"
        
        $confirmation = Read-Host "`nDo you want to continue? (y/N)"
        if ($confirmation -notmatch '^[Yy]') {
            Write-ColorOutput "Release cancelled by user." "Warning"
            exit 0
        }
    }
    
    Write-ColorOutput "`n Starting release process..." "Header"
    
    # Step 1: Remove build directory
    Write-ColorOutput "`n[1/3] Cleaning build directory" "Header"
    Remove-BuildDirectory -BuildPath $buildPath
    
    # Step 2: Compress dist directory
    Write-ColorOutput "`n[2/3] Compressing dist directory" "Header"
    Compress-DistDirectory -DistPath $distPath -OutputPath $archivePath -Version $version
    
    # Step 3: Create GitHub release
    Write-ColorOutput "`n[3/3] Creating GitHub release" "Header"
    $releaseSuccess = New-GitHubRelease -Version $version -ArchivePath $archivePath
    
    if ($releaseSuccess) {
        Write-ColorOutput "`n Release process completed successfully!" "Success"
        Write-ColorOutput "======================================" "Header"
        Write-ColorOutput "Version: $version" "Success"
        Write-ColorOutput "Archive: $archivePath" "Success"
        Write-ColorOutput "GitHub release created and archive uploaded" "Success"
    } else {
        Write-ColorOutput "`n Release process failed during GitHub release creation" "Error"
        exit 1
    }
    
} catch {
    Write-ColorOutput "`n Release process failed: $_" "Error"
    Write-ColorOutput "Stack trace:" "Error"
    Write-ColorOutput $_.ScriptStackTrace "Error"
    exit 1
}

Write-ColorOutput "`n Script execution completed." "Header"

<#
.SYNOPSIS
    UWBDash自动化发布脚本

.EXAMPLE
    .\release.ps1
    使用默认设置运行发布脚本，会提示用户确认。

.EXAMPLE
    .\release.ps1 -SkipConfirm
    跳过确认提示，直接执行发布流程。

.EXAMPLE
    .\release.ps1 -Force
    如果Release已存在，强制覆盖并重新创建。

.EXAMPLE
    .\release.ps1 -CustomVersion "v2.1.0" -SkipConfirm
    使用自定义版本号v2.1.0，跳过确认提示。

.EXAMPLE
    .\release.ps1 -Force -SkipConfirm -CustomVersion "v2.1.0"
    组合使用所有参数：使用自定义版本，强制覆盖，跳过确认。

.NOTES
    文件名: release.ps1
    作者: @Qilang²
    版本: 1.0
    创建日期: 2025-01-16
    
    前置条件:
    - 已安装GitHub CLI (gh)
    - 已登录GitHub CLI (gh auth login)
    - 当前目录为Git仓库
    - PowerShell 5.0或更高版本
#>