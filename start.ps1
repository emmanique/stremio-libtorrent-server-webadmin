$ErrorActionPreference = 'Stop'
Set-StrictMode -Version 2.0

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

function Get-PreferredIPv4 {
    if ($env:IPADDRESS) { return $env:IPADDRESS }

    try {
        $udp = New-Object System.Net.Sockets.UdpClient
        $udp.Connect('1.1.1.1', 53)
        $endpoint = [System.Net.IPEndPoint]$udp.Client.LocalEndPoint
        $ip = $endpoint.Address.IPAddressToString
        $udp.Dispose()
        if ($ip) { return $ip }
    } catch {
        try { if ($udp) { $udp.Dispose() } } catch {}
    }

    try {
        $cfg = Get-NetIPConfiguration |
            Where-Object { $_.IPv4DefaultGateway -and $_.IPv4Address } |
            Sort-Object { $_.NetIPv4Interface.RouteMetric } |
            Select-Object -First 1
        if ($cfg) { return $cfg.IPv4Address.IPAddress }
    } catch {}

    return $null
}

function Test-IPv4([string]$Address) {
    $parsed = $null
    if (-not [System.Net.IPAddress]::TryParse($Address, [ref]$parsed)) { return $false }
    return $parsed.AddressFamily -eq [System.Net.Sockets.AddressFamily]::InterNetwork
}

function Test-ContainerExists([string]$Name) {
    & docker container inspect $Name *> $null
    return $LASTEXITCODE -eq 0
}

function Invoke-Compose([string[]]$ComposeArgs) {
    $dockerArgs = @('compose') + $ComposeArgs
    & docker @dockerArgs
    return $LASTEXITCODE
}

$ip = Get-PreferredIPv4
if (-not $ip -or -not (Test-IPv4 $ip)) {
    Write-Error '[start] unable to determine a valid host IPv4 address. Set $env:IPADDRESS, e.g. $env:IPADDRESS="192.168.1.244"; .\start.ps1'
    exit 1
}

$env:IPADDRESS = $ip
if (-not $env:PIHOLE_WEB_BIND_IP) { $env:PIHOLE_WEB_BIND_IP = $ip }
if (-not $env:PIHOLE_DNS_BIND_IP) { $env:PIHOLE_DNS_BIND_IP = $ip }

Write-Host "[start] detected host IPv4: $ip"
Write-Host "[start] Web Player : http://${ip}:8080"
Write-Host "[start] WebAdmin   : http://${ip}:8090"
Write-Host "[start] API        : http://${ip}:11470"
Write-Host "[start] Library    : https://${ip}:12470/library/"
Write-Host "[start] Pi-hole    : http://$($env:PIHOLE_WEB_BIND_IP):8053/admin/"

& docker compose version *> $null
if ($LASTEXITCODE -ne 0) {
    Write-Error '[start] Docker Compose is not available. Install/start Docker Desktop and use Linux containers.'
    exit 1
}

if ($args.Count -eq 0) {
    Write-Host '[start] pulling published images...'
    $rc = Invoke-Compose @('pull')
    if ($rc -ne 0) { exit $rc }

    if (Test-ContainerExists 'stremio-gluetun') {
        Write-Host '[start] switching VPN -> direct mode (persistent volumes are preserved)...'
        & docker rm -f stremio-libtorrent-server *> $null
        & docker rm -f stremio-gluetun *> $null
    }

    $rc = Invoke-Compose @('up', '-d', '--remove-orphans')
    exit $rc
}

$rc = Invoke-Compose $args
exit $rc
