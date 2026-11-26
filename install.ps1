# Installation clé en main de TripoSG (Windows + GPU NVIDIA). Lancer via installer.bat
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
$TRIPOSG_COMMIT = "fc5c40990181e2a756c4e0b1c2f4d6b5202faf8c"  # version testée du dépôt officiel

function Step($msg) { Write-Host "`n=== $msg ===" -ForegroundColor Cyan }
function Fail($msg) { Write-Host "`nERREUR : $msg" -ForegroundColor Red; exit 1 }

Step "Vérification des prérequis"
if (-not (Get-Command git -ErrorAction SilentlyContinue)) { Fail "Git n'est pas installé : https://git-scm.com/download/win" }
if (-not (Get-Command nvidia-smi -ErrorAction SilentlyContinue)) { Fail "Pilote NVIDIA introuvable (nvidia-smi). Une carte NVIDIA est obligatoire." }
$gpu = (nvidia-smi --query-gpu=name,memory.total --format=csv,noheader,nounits | Select-Object -First 1).Split(",")
Write-Host "GPU : $($gpu[0].Trim()) ($($gpu[1].Trim()) Mo)"
if ([int]$gpu[1] -lt 7900) { Write-Host "Attention : moins de 8 Go de VRAM, ça risque de manquer de mémoire." -ForegroundColor Yellow }
if ($gpu[0] -match "RTX 50[5-9]0") { Fail "Les RTX 50xx ne sont pas supportées par cette version (PyTorch 2.5 / CUDA 12.1)." }

$py = $null  # chemin complet d'un python 3.10
foreach ($cand in @(@("py", "-3.10"), @("python"))) {
    if (-not (Get-Command $cand[0] -ErrorAction SilentlyContinue)) { continue }
    try { $out = & $cand[0] ($cand | Select-Object -Skip 1) -c "import sys;print('%d.%d' % sys.version_info[:2], sys.executable)" 2>&1 } catch { continue }
    if ("$out" -match '^3\.10 (.+)$') { $py = $Matches[1].Trim(); break }
}
if (-not $py) { Fail "Python 3.10 est requis : https://www.python.org/downloads/release/python-31011/ (cocher 'Add to PATH')" }
Write-Host "Python : $py"

Step "Téléchargement du code des modèles"
$repos = @(
    @("TripoSG", "https://github.com/VAST-AI-Research/TripoSG", $TRIPOSG_COMMIT),
    @("TripoSR", "https://github.com/VAST-AI-Research/TripoSR", "107cefdc244c39106fa830359024f6a2f1c78871"),
    @("sf3d", "https://github.com/Stability-AI/stable-fast-3d", "ff21fc491b4dc5314bf6734c7c0dabd86b5f5bb2")
)
foreach ($r in $repos) {
    if (-not (Test-Path "$($r[0])\.git")) { git clone $r[1] $r[0]; if ($LASTEXITCODE) { Fail "git clone de $($r[0]) a échoué" } }
    git -C $r[0] checkout -q $r[2]; if ($LASTEXITCODE) { Fail "git checkout de $($r[0]) a échoué" }
}

Step "Création de l'environnement Python"
if (-not (Test-Path ".venv\Scripts\python.exe")) { & $py -m venv .venv; if ($LASTEXITCODE) { Fail "création du venv impossible" } }
$vpy = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
& $vpy -m pip install -q --upgrade pip

Step "Installation des dépendances (~3 Go, plusieurs minutes)"
& $vpy -m pip install -r requirements-lock.txt; if ($LASTEXITCODE) { Fail "pip install a échoué (voir les messages au-dessus)" }

Step "Vérification de l'installation"
& $vpy -c "import torch, diso, torchmcubes, texture_baker, uv_unwrapper; assert torch.cuda.is_available(), 'CUDA indisponible'; print('torch', torch.__version__, '-', torch.cuda.get_device_name(0))"
if ($LASTEXITCODE) { Fail "PyTorch ne voit pas le GPU. Mets à jour le pilote NVIDIA." }

Step "Téléchargement des poids de TripoSG (~8 Go ; les autres modèles se téléchargent à leur premier usage)"
& $vpy -c "from huggingface_hub import snapshot_download as d; d('VAST-AI/TripoSG', local_dir='pretrained_weights/TripoSG'); d('briaai/RMBG-1.4', local_dir='pretrained_weights/RMBG-1.4')"
if ($LASTEXITCODE) { Fail "téléchargement des poids impossible (connexion ?). Relance installer.bat, il reprendra." }

Write-Host "`nInstallation terminée ! Double-clique sur lancer.bat pour ouvrir l'interface." -ForegroundColor Green
