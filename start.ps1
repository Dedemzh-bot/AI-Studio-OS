$ErrorActionPreference = "Stop"
Set-Location -LiteralPath $PSScriptRoot

$candidates = @(
    (Join-Path $PSScriptRoot ".venv\Scripts\python.exe"),
    (Join-Path $PSScriptRoot "venv\Scripts\python.exe")
)

$python = $null
foreach ($candidate in $candidates) {
    if (Test-Path -LiteralPath $candidate) {
        & $candidate -c "import sys; raise SystemExit(sys.version_info < (3, 10))" *> $null
        if ($LASTEXITCODE -eq 0) {
            $python = $candidate
            break
        }
    }
}

if (-not $python) {
    $commonRoots = @(
        (Join-Path $env:LOCALAPPDATA "Programs\Python"),
        $env:ProgramFiles,
        ${env:ProgramFiles(x86)}
    ) | Where-Object { $_ -and (Test-Path -LiteralPath $_) }

    foreach ($root in $commonRoots) {
        $found = Get-ChildItem -Path $root -Filter python.exe -File -Recurse -Depth 3 -ErrorAction SilentlyContinue |
            Select-Object -ExpandProperty FullName
        foreach ($candidate in $found) {
            & $candidate -c "import sys; raise SystemExit(sys.version_info < (3, 10))" *> $null
            if ($LASTEXITCODE -eq 0) {
                $python = $candidate
                break
            }
        }
        if ($python) { break }
    }
}

if (-not $python) {
    $py = Get-Command py -ErrorAction SilentlyContinue
    if ($py) {
        & $py.Source -3 -c "import sys; print(sys.executable)" *> $null
        if ($LASTEXITCODE -eq 0) {
            $python = "$($py.Source) -3"
        }
    }
}

if (-not $python) {
    $cmd = Get-Command python -ErrorAction SilentlyContinue
    if ($cmd) {
        & $cmd.Source -c "import sys; raise SystemExit(sys.version_info < (3, 10))" *> $null
        if ($LASTEXITCODE -eq 0) {
            $python = $cmd.Source
        }
    }
}

if (-not $python) {
    Write-Host "Python 3.10+ was not found." -ForegroundColor Red
    Write-Host "Install Python with Add Python to PATH enabled, or create a project .venv."
    Write-Host "Then run: python -m pip install -r requirements.txt"
    exit 1
}

Write-Host "AI Studio OS - http://localhost:8080"
if ($python.EndsWith(" -3")) {
    $launcher = $python.Substring(0, $python.Length - 3)
    & $launcher -3 server.py
} else {
    & $python server.py
}
