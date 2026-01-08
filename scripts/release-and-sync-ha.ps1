param(
    [string]$Version,
    [string]$HaRepoPath = "C:\Users\AlexRasmussen\src\mycousinvinyl-ha",
    [switch]$SkipHa,
    [switch]$Force
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Get-RepoRoot {
    $root = Resolve-Path (Join-Path $PSScriptRoot "..")
    return $root.Path
}

function Parse-Version {
    param([string]$Value)
    $clean = $Value.Trim()
    if ($clean.StartsWith("v")) {
        $clean = $clean.Substring(1)
    }
    if ($clean -notmatch '^\d+\.\d+\.\d+$') {
        throw "Unsupported version format: $Value (expected vX.Y.Z)"
    }
    return [Version]$clean
}

function Get-LatestTagLocal {
    $tags = git tag --list "v*"
    if (-not $tags) {
        return $null
    }
    $parsed = @()
    foreach ($tag in $tags) {
        if ($tag -match '^v\d+\.\d+\.\d+$') {
            $parsed += [pscustomobject]@{
                Tag = $tag
                Version = Parse-Version $tag
            }
        }
    }
    if ($parsed.Count -eq 0) {
        return $null
    }
    return ($parsed | Sort-Object Version -Descending | Select-Object -First 1).Tag
}

function Normalize-TagName {
    param([string]$Value)
    $clean = $Value.Trim()
    if (-not $clean.StartsWith("v")) {
        $clean = "v$clean"
    }
    Parse-Version $clean | Out-Null
    return $clean
}

function Assert-GitClean {
    $status = git status --porcelain
    if ($status) {
        throw "Working tree has uncommitted changes. Commit/push before releasing."
    }
}

$repoRoot = Get-RepoRoot
Push-Location $repoRoot
try {
    if (-not (Test-Path (Join-Path $repoRoot ".git"))) {
        throw "Not a git repo: $repoRoot"
    }

    Assert-GitClean

    $originUrl = git remote get-url origin
    if (-not $originUrl) {
        throw "No origin remote found."
    }

    if (-not $Version) {
        $latestTag = Get-LatestTagLocal
        if (-not $latestTag) {
            throw "No local tags found. Pass -Version vX.Y.Z."
        }
        $latestVersion = Parse-Version $latestTag
        $nextVersion = New-Object System.Version($latestVersion.Major, $latestVersion.Minor, $latestVersion.Build + 1)
        $suggested = "v$nextVersion"
        $input = Read-Host "Release tag (default $suggested)"
        if ($input) {
            $Version = $input
        } else {
            $Version = $suggested
        }
    }

    $tagName = Normalize-TagName $Version
    $existing = git tag --list $tagName
    if ($existing) {
        throw "Tag already exists: $tagName"
    }

    Write-Host "Pushing current branch..."
    git push

    Write-Host "Creating release tag $tagName..."
    git tag -a $tagName -m "Release $tagName"
    git push origin $tagName

    if (-not $SkipHa) {
        $haScript = Join-Path $HaRepoPath "scripts\update-from-app.ps1"
        if (-not (Test-Path $haScript)) {
            throw "HA update script not found: $haScript"
        }
        Write-Host "Syncing HA repo from $originUrl..."
        & $haScript -AppRepoUrl $originUrl -Force:$Force
    }
} finally {
    Pop-Location
}
