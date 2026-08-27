<#
    Equivalent PowerShell du Makefile — `make` n'est pas installe par defaut
    sur Windows. Memes noms de cibles que le Makefile.

    Usage :   .\make.ps1 install
              .\make.ps1 dev
              .\make.ps1            (affiche l'aide)

    Si la politique d'execution bloque le script :
              powershell -ExecutionPolicy Bypass -File .\make.ps1 dev
#>

param(
    [Parameter(Position = 0)]
    [string]$Target = "help"
)

$ErrorActionPreference = "Stop"
Set-Location -Path $PSScriptRoot

# 8010 par defaut : le port 8000 est occupe par des regles netsh portproxy (WSL).
$PortApi  = if ($env:FP_PORT) { $env:FP_PORT } else { 8010 }
$PortUser = 5173
$PortDeck = 5174
$AdminToken = if ($env:FP_ADMIN_TOKEN) { $env:FP_ADMIN_TOKEN } else { "loreal2026" }

function Get-LanIp {
    try {
        $socket = New-Object System.Net.Sockets.Socket('InterNetwork', 'Dgram', 'Udp')
        $socket.Connect('8.8.8.8', 80)
        $ip = $socket.LocalEndPoint.Address.ToString()
        $socket.Dispose()
        return $ip
    } catch {
        return "127.0.0.1"
    }
}

function Invoke-Admin([string]$Path, [string]$JsonBody) {
    Invoke-RestMethod -Method Post -Uri "http://localhost:$PortApi$Path" `
        -Headers @{ "X-Admin-Token" = $AdminToken } `
        -ContentType "application/json" -Body $JsonBody | ConvertTo-Json -Compress
}

switch ($Target.ToLower()) {

    "help" {
        Write-Host ""
        Write-Host "  final_presentation - cibles disponibles" -ForegroundColor Yellow
        Write-Host "  ---------------------------------------"
        Write-Host "  install      Cree .venv et installe les dependances (uv)"
        Write-Host "  dev          Lance TOUT en local (API + deck + app participant)"
        Write-Host "  back         Lance uniquement l'API FastAPI"
        Write-Host "  serve-user   Sert frontend_user seul sur le port $PortUser"
        Write-Host "  serve-deck   Sert frontend_main seul sur le port $PortDeck"
        Write-Host "  test         Lance les tests backend"
        Write-Host "  lint         Verifie le style (ruff)"
        Write-Host "  format       Corrige le style (ruff)"
        Write-Host "  ip           Affiche l'IP LAN a donner aux telephones"
        Write-Host "  qr           Genere static/qr/join.png"
        Write-Host "  qr-lan       Genere le QR pointant vers l'IP LAN"
        Write-Host "  seed         Injecte 25 faux participants"
        Write-Host "  reset        Remet la session a zero"
        Write-Host "  clean        Supprime .venv, caches et QR generes"
        Write-Host ""
        Write-Host "  Selon ton shell :" -ForegroundColor DarkGray
        Write-Host "    Git Bash    ./make.sh <cible>" -ForegroundColor DarkGray
        Write-Host "    PowerShell  .\make.ps1 <cible>" -ForegroundColor DarkGray
        Write-Host "    cmd.exe     make <cible>" -ForegroundColor DarkGray
        Write-Host ""
    }

    "install" {
        uv venv
        uv sync --all-groups
        Write-Host ""
        Write-Host "Environnement pret. Lance maintenant : .\make.ps1 dev" -ForegroundColor Green
    }

    { $_ -in @("dev", "back") } {
        $ip = Get-LanIp
        Write-Host ""
        Write-Host "  Deck presentateur : http://localhost:$PortApi/deck" -ForegroundColor Cyan
        Write-Host "  App participant   : http://localhost:$PortApi/app" -ForegroundColor Cyan
        Write-Host "  Depuis un telephone du meme wifi : http://${ip}:$PortApi/app" -ForegroundColor Cyan
        Write-Host "  Doc API           : http://localhost:$PortApi/docs"
        Write-Host ""
        uv run uvicorn app.main:app --app-dir backend --reload --host 0.0.0.0 --port $PortApi
    }

    "serve-user" {
        uv run python -m http.server $PortUser --directory frontend_user --bind 0.0.0.0
    }

    "serve-deck" {
        uv run python -m http.server $PortDeck --directory frontend_main --bind 0.0.0.0
    }

    "test"   { uv run pytest -q }
    "lint"   { uv run ruff check backend scripts }
    "format" { uv run ruff check --fix backend scripts; uv run ruff format backend scripts }

    "ip" {
        $ip = Get-LanIp
        Write-Host "IP LAN : $ip" -ForegroundColor Green
        Write-Host "App participant depuis un telephone : http://${ip}:$PortApi/app"
    }

    "qr"     { uv run python scripts/gen_qr.py }
    "qr-lan" { uv run python scripts/gen_qr.py }   # le defaut vise deja l'IP LAN

    "seed"   { Invoke-Admin "/api/admin/seed" '{"participants": 25}' }
    "reset"  { Invoke-Admin "/api/admin/reset" '{}' }

    "clean" {
        foreach ($dir in @(".venv", ".pytest_cache", ".ruff_cache")) {
            if (Test-Path $dir) { Remove-Item -Recurse -Force $dir }
        }
        Get-ChildItem "static/qr" -Filter *.png -ErrorAction SilentlyContinue | Remove-Item -Force
        Write-Host "Nettoye." -ForegroundColor Green
    }

    default {
        Write-Host "Cible inconnue : $Target" -ForegroundColor Red
        Write-Host "Lance .\make.ps1 help pour la liste."
        exit 1
    }
}
