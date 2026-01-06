# PowerShell script to deploy to the local docker desktop
# Usage: .\deploy-to-nas.ps1 [--build] [module]

param(
    [switch]$Build,
    [string]$Module
)


$env:MQTT_URL = "mqtt://10.254.1.160:1883"
$env:MQTT_USERNAME = "mqtt"
$env:MQTT_PASSWORD = "CaJo2010"

$composeArgs = @("compose", "-f", "docker-compose.yml", "-f", "docker-compose.external-mqtt.yml", "up", "-d")
if ($Build) {
    $composeArgs += "--build"
}
if ($Module -and $Module.Trim()) {
    $composeArgs += $Module
}

docker @composeArgs
