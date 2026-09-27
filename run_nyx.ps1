# ==============================================================================
# Nyx AGI Desktop v3 — Script de Inicialização Automatizada para Windows 11
# ==============================================================================
# Executa pré-checagens de GPU (RTX 3060), ativa ambiente virtual, verifica Ollama,
# assegura limites de VRAM e inicia a interface de overlay/agente.
# ==============================================================================

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$Host.UI.RawUI.WindowTitle = "Nyx AGI Desktop — O Grande Sábio"

Write-Host "════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  🔮 INICIANDO NYX AGI DESKTOP v3 (O GRANDE SÁBIO)             " -ForegroundColor Cyan
Write-Host "════════════════════════════════════════════════════════════════" -ForegroundColor Cyan

# 1. Checagem de GPU e Driver NVIDIA
Write-Host "`n[1/4] Verificando hardware e GPU NVIDIA..." -ForegroundColor Yellow
if (Get-Command nvidia-smi -ErrorAction SilentlyContinue) {
    $gpuInfo = nvidia-smi --query-gpu=name,memory.total,memory.free,driver_version --format=csv,noheader
    Write-Host "  [OK] GPU Detectada: $gpuInfo" -ForegroundColor Green
} else {
    Write-Host "  [AVISO] 'nvidia-smi' não encontrado no PATH. Modo CPU fallback será utilizado." -ForegroundColor DarkYellow
}

# 2. Checagem do Servidor Ollama
Write-Host "`n[2/4] Verificando servidor Ollama local..." -ForegroundColor Yellow
try {
    $ollamaCheck = Invoke-RestMethod -Uri "http://127.0.0.1:11434/api/tags" -Method Get -TimeoutSec 3 -ErrorAction Stop
    $models = $ollamaCheck.models | ForEach-Object { $_.name }
    Write-Host "  [OK] Ollama ativo. Modelos disponíveis: $($models -join ', ')" -ForegroundColor Green
} catch {
    Write-Host "  [AVISO] Servidor Ollama não respondeu em 127.0.0.1:11434." -ForegroundColor DarkYellow
    Write-Host "  Iniciando Ollama em segundo plano..." -ForegroundColor DarkGray
    Start-Process "ollama" -ArgumentList "serve" -WindowStyle Hidden -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 2
}

# 3. Verificação do Ambiente Virtual Python
Write-Host "`n[3/4] Configurando ambiente virtual Python..." -ForegroundColor Yellow
$VENV_PYTHON = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"

if (-not (Test-Path $VENV_PYTHON)) {
    Write-Host "  Ambiente virtual não encontrado. Criando com uv..." -ForegroundColor DarkGray
    if (Get-Command uv -ErrorAction SilentlyContinue) {
        uv venv .venv
        uv pip install -r requirements.txt
    } else {
        python -m venv .venv
        & $VENV_PYTHON -m pip install -r requirements.txt
    }
}

Write-Host "  [OK] Interpretador Python configurado: $VENV_PYTHON" -ForegroundColor Green

# 4. Variáveis de Ambiente e Inicialização
Write-Host "`n[4/4] Subindo Nyx AGI Desktop..." -ForegroundColor Yellow
$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"
$env:OLLAMA_MAX_LOADED_MODELS = "1"
$env:OLLAMA_FLASH_ATTENTION = "1"

Write-Host "  Disparando interface gráfica e agentes..." -ForegroundColor Green
& $VENV_PYTHON src/main.py @args
