# Script para atualizar IP do Duck DNS
param (
    [string]$Domain,
    [string]$Token,
    [string]$Ip
)

# Carrega do .env caso não seja passado por parâmetro
if (-not $Domain -or -not $Token) {
    $envFile = Join-Path $PSScriptRoot "..\.env"
    if (Test-Path $envFile) {
        Get-Content $envFile | ForEach-Object {
            $line = $_.Trim()
            if ($line -and -not $line.StartsWith("#") -and $line.Contains("=")) {
                $parts = $line -split "=", 2
                $k = $parts[0].Trim()
                $v = $parts[1].Trim()
                if ($k -eq "DUCKDNS_DOMAIN" -and -not $Domain) { $Domain = $v }
                if ($k -eq "DUCKDNS_TOKEN" -and -not $Token) { $Token = $v }
                if ($k -eq "DUCKDNS_IP" -and -not $Ip) { $Ip = $v }
            }
        }
    }
}

if (-not $Domain) { $Domain = "workana" }
if (-not $Ip) { $Ip = "179.180.50.157" }

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "       ATUALIZADOR DUCK DNS              " -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "Dominio: $Domain.duckdns.org"
Write-Host "IP Alvo: $Ip"

if (-not $Token -or $Token -eq "seu_token_duckdns") {
    Write-Host "[ALERTA] Token do Duck DNS nao configurado!" -ForegroundColor Yellow
    Write-Host "Configure DUCKDNS_TOKEN no arquivo .env com seu token de https://www.duckdns.org" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "URL direta para atualizar no navegador:" -ForegroundColor Green
    Write-Host "https://www.duckdns.org/update?domains=$Domain&token=SEU_TOKEN&ip=$Ip" -ForegroundColor Green
    Write-Host ""
    exit 1
}

$updateUrl = "https://www.duckdns.org/update?domains=$Domain&token=$Token&ip=$Ip"

try {
    Write-Host "Enviando requisicao de atualizacao para Duck DNS..." -ForegroundColor Gray
    $response = Invoke-RestMethod -Uri $updateUrl -Method Get -TimeoutSec 10
    if ($response -eq "OK") {
        Write-Host "[SUCESSO] IP atualizado com sucesso no Duck DNS!" -ForegroundColor Green
        Write-Host "Dominio: http://$Domain.duckdns.org -> $Ip" -ForegroundColor Green
    } else {
        Write-Host "[RESPOSTA DUCKDNS] $response" -ForegroundColor Yellow
    }
} catch {
    Write-Host "[ERRO] Falha ao contatar Duck DNS: $_" -ForegroundColor Red
}
