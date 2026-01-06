# PowerShell script to deploy to NAS using SSH/SCP with password authentication
# Usage: .\deploy-to-nas.ps1 -Build

param(
    [string]$NasHost = $env:SYNOLOGY_HOST,
    [string]$NasUser = $env:SYNOLOGY_USER,
    [string]$NasPassword = $env:SYNOLOGY_PASSWORD,
    [string]$PuttySession = $env:SYNOLOGY_PUTTY_SESSION,
    [string]$PuttyKeyPath = $env:SYNOLOGY_PUTTY_KEY,
    [string]$ProjectPath = "/docker/mycousinvinyl",
    [string]$ComposeFile = "docker-compose.nas.yml",
    [string]$EnvFile = ".env.nas",
    [switch]$Build = $false
)

if (-not $NasHost) {
    $NasHost = $env:NAS_HOST
}

if (-not $NasHost) {
    $NasHost = "10.254.1.210"
}

Write-Host "=== MyCousinVinyl Deployment to NAS ===" -ForegroundColor Cyan
Write-Host ""

if (-not $NasUser) {
    Write-Error "SYNOLOGY_USER environment variable is not set"
    exit 1
}

if (-not (Test-Path $ComposeFile)) {
    Write-Error "Compose file not found: $ComposeFile"
    exit 1
}

$plinkCmd = Get-Command plink -ErrorAction SilentlyContinue
$pscpCmd = Get-Command pscp -ErrorAction SilentlyContinue
$sshCmd = Get-Command ssh -ErrorAction SilentlyContinue
$scpCmd = Get-Command scp -ErrorAction SilentlyContinue

$usePutty = $false
if ($plinkCmd -and $pscpCmd) {
    $usePutty = $true
}
elseif (-not ($sshCmd -and $scpCmd)) {
    Write-Error "No SSH/SCP client found. Install OpenSSH or PuTTY (plink/pscp)."
    exit 1
}

if (-not $usePutty) {
    Write-Host "Using OpenSSH; you may be prompted for the NAS password." -ForegroundColor Yellow
}
else {
    Write-Host "Using PuTTY (plink/pscp) for SSH/SCP." -ForegroundColor Yellow
}

Write-Host "Target NAS: $NasHost" -ForegroundColor Green
Write-Host "Deploy path: $ProjectPath" -ForegroundColor Green
Write-Host "Compose file: $ComposeFile" -ForegroundColor Green
Write-Host ""

function Get-PuttyAuthArgs {
    if ($PuttySession) {
        return @("-load", $PuttySession)
    }
    if ($PuttyKeyPath) {
        return @("-i", $PuttyKeyPath)
    }
    if (-not $NasPassword) {
        throw "SYNOLOGY_PASSWORD is not set and no PuTTY session/key was provided."
    }
    return @("-pw", $NasPassword)
}

function Copy-Remote {
    param(
        [string]$Source,
        [string]$Destination
    )

    $isDirectory = (Get-Item $Source).PSIsContainer

    if ($usePutty) {
        $args = @()
        if ($isDirectory) {
            $args += "-r"
        }
        $args += Get-PuttyAuthArgs
        $args += $Source
        $args += "${NasUser}@${NasHost}:$Destination"
        & $pscpCmd.Path @args
    }
    else {
        $args = @()
        if ($isDirectory) {
            $args += "-r"
        }
        $args += "-o"
        $args += "StrictHostKeyChecking=no"
        $args += $Source
        $args += "${NasUser}@${NasHost}:$Destination"
        & $scpCmd.Path @args
    }

    if ($LASTEXITCODE -ne 0) {
        throw "Failed to copy $Source to $Destination"
    }
}

function Invoke-RemoteScript {
    param(
        [string]$ScriptPath
    )

    if ($usePutty) {
        $authArgs = Get-PuttyAuthArgs
        & $plinkCmd.Path @authArgs -ssh "$NasUser@$NasHost" -m $ScriptPath
    }
    else {
        $scriptContent = Get-Content -Path $ScriptPath -Raw
        $scriptContent | & $sshCmd.Path -o StrictHostKeyChecking=no "$NasUser@$NasHost" "sh -s"
    }

    if ($LASTEXITCODE -ne 0) {
        throw "Remote command failed."
    }
}

$tempMkdir = $null
$tempRemote = $null

try {
    Write-Host "Step 1: Copying project files to NAS..." -ForegroundColor Yellow

    $itemsToCopy = @(
        "backend",
        "frontend",
        "infrastructure",
        "discogs-service",
        $ComposeFile
    )

    foreach ($item in $itemsToCopy) {
        if (Test-Path $item) {
            Write-Host "Copying $item..."
            Copy-Remote -Source $item -Destination "$ProjectPath/"
        }
        else {
            Write-Warning "Skipping missing item: $item"
        }
    }

    $envSource = $null
    if (Test-Path $EnvFile) {
        $envSource = $EnvFile
    }
    elseif (Test-Path ".env") {
        $envSource = ".env"
    }

    if ($envSource) {
        Write-Host "Copying environment file ($envSource) to NAS..." -ForegroundColor Yellow
        Copy-Remote -Source $envSource -Destination "$ProjectPath/.env"
    }
    else {
        Write-Warning "No .env.nas or .env found. Configure environment variables on the NAS."
    }

    Write-Host "Step 2: Starting Docker containers on NAS..." -ForegroundColor Yellow

    $composeFileName = Split-Path $ComposeFile -Leaf
    $buildFlag = if ($Build) { "true" } else { "false" }
    $nasPasswordEscaped = ""
    if ($NasPassword) {
        $replacement = "'" + '"' + "'" + '"' + "'"
        $nasPasswordEscaped = $NasPassword -replace "'", $replacement
    }

    $remoteScript = @'
set -e
cd "/volume1{0}"

if [ ! -f ".env" ] && [ -f ".env.example" ]; then
  cp .env.example .env
fi

export PATH="/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:$PATH"

NAS_SUDO_PASSWORD='{1}'

sudo_cmd() {{
  if [ -n "$NAS_SUDO_PASSWORD" ]; then
    printf '%s\n' "$NAS_SUDO_PASSWORD" | sudo -S env PATH="/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:$PATH" "$@"
  else
    sudo env PATH="/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:$PATH" "$@"
  fi
}}

compose_cmd() {{
  if command -v docker-compose >/dev/null 2>&1; then
    echo "$(command -v docker-compose)"
    return
  fi
  if command -v docker >/dev/null 2>&1; then
    echo "$(command -v docker) compose"
    return
  fi
  echo "docker compose"
}}

COMPOSE_CMD="$(compose_cmd)"

if [ "{2}" = "true" ]; then
  echo "Building Docker images..."
  sudo_cmd $COMPOSE_CMD -f "{3}" build --build-arg VITE_NPM_BUILD_SCRIPT=build:nas --build-arg VITE_MANIFEST_ENV=nas
else
  echo "Pulling Docker images..."
  sudo_cmd $COMPOSE_CMD -f "{3}" pull || true
fi

sudo_cmd $COMPOSE_CMD -f "{3}" down
sudo_cmd $COMPOSE_CMD -f "{3}" up -d
sudo_cmd $COMPOSE_CMD -f "{3}" ps
'@ -f $ProjectPath, $nasPasswordEscaped, $buildFlag, $composeFileName

    $tempRemote = Join-Path $PSScriptRoot "temp_nas_deploy.sh"
    $remoteScriptLf = $remoteScript -replace "\r\n", "\n"
    [System.IO.File]::WriteAllText($tempRemote, $remoteScriptLf, [System.Text.ASCIIEncoding]::new())
    Invoke-RemoteScript -ScriptPath $tempRemote

    Write-Host ""
    Write-Host "=== Deployment Complete ===" -ForegroundColor Green
    Write-Host ""
    Write-Host "Services should be available at:" -ForegroundColor Cyan
    Write-Host "  Frontend: http://$NasHost:3000"
    Write-Host "  Backend API: http://$NasHost:8000"
    Write-Host "  ActiveMQ Admin: http://$NasHost:8161"
    Write-Host ""
    Write-Host "To view logs, run:" -ForegroundColor Yellow
    Write-Host "  ssh $NasUser@$NasHost 'cd $ProjectPath && docker-compose -f $composeFileName logs -f'"
    Write-Host ""
}
catch {
    Write-Error "Deployment failed: $_"
    exit 1
}
finally {
    if ($tempMkdir -and (Test-Path $tempMkdir)) {
        Remove-Item $tempMkdir -ErrorAction SilentlyContinue
    }
    if ($tempRemote -and (Test-Path $tempRemote)) {
        Remove-Item $tempRemote -ErrorAction SilentlyContinue
    }
}
