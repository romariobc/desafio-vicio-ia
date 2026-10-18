param([string]$Python = '')
$ErrorActionPreference = 'Stop'
$env:PYTHONIOENCODING = 'utf-8'
if (-not $Python) {
    $candidate = Get-Command python -ErrorAction SilentlyContinue
    if ($candidate) { $Python = $candidate.Source }
    else {
        $bundledPython = Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
        if (Test-Path -LiteralPath $bundledPython) { $Python = $bundledPython }
        else { throw 'Informe -Python com o caminho do Python 3.10 ou superior.' }
    }
}
$watch = [System.Diagnostics.Stopwatch]::StartNew()
Push-Location $PSScriptRoot
try {
    foreach ($script in @('preparar.py','referencia.py','pipeline.py','relatorio.py')) {
        & $Python $script
        if ($LASTEXITCODE -ne 0) { throw "Falha em $script" }
    }
    & $Python -m unittest discover -s . -p test_pipeline.py -v
    if ($LASTEXITCODE -ne 0) { throw 'Falha nos testes' }
    $watch.Stop()
    Write-Output ('Reprodução local e testes: {0:N2} segundos. Não inclui nova inferência GPT.' -f $watch.Elapsed.TotalSeconds)
} finally { Pop-Location }
