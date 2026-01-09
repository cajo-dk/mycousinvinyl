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

function Get-ReleaseTitle {
    param([string]$TagName)
    $subject = git log -1 --pretty=%s
    if (-not $subject) {
        throw "Unable to read latest commit message."
    }
    return "$TagName - $subject"
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

function Assert-GhAvailable {
    if (-not (Get-Command gh -ErrorAction SilentlyContinue)) {
        throw "GitHub CLI not found. Install gh to create releases."
    }
}

function Create-Release {
    param(
        [string]$RepoPath,
        [string]$TagName,
        [string]$Title,
        [string]$Notes
    )
    Push-Location $RepoPath
    try {
        $existing = gh release view $TagName 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "Release already exists for $TagName in $RepoPath. Skipping."
            return
        }
        Write-Host "Creating release $TagName in $RepoPath..."
        gh release create $TagName --title $Title --notes $Notes | Out-Null
    } finally {
        Pop-Location
    }
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
        if ($latestVersion.Revision -ge 0) {
            throw "Latest tag uses a 4-part version. Please pass -Version vX.Y.Z."
        }
        $suggested = "v$($latestVersion.Major).$($latestVersion.Minor).$($latestVersion.Build + 1)"
        $input = Read-Host "Release tag (default $suggested)"
        if ($input) {
            $Version = $input
        } else {
            $Version = $suggested
        }
    }

    Assert-GhAvailable

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
    $releaseTitle = Get-ReleaseTitle -TagName $tagName
    Create-Release -RepoPath $repoRoot -TagName $tagName -Title $releaseTitle -Notes $releaseTitle

    if (-not $SkipHa) {
        $haScript = Join-Path $HaRepoPath "scripts\update-from-app.ps1"
        if (-not (Test-Path $haScript)) {
            throw "HA update script not found: $haScript"
        }
        Write-Host "Syncing HA repo from $originUrl..."
        & $haScript -AppRepoUrl $originUrl -Force:$Force
        Create-Release -RepoPath $HaRepoPath -TagName $tagName -Title $releaseTitle -Notes $releaseTitle
    }
} finally {
    Pop-Location
}
