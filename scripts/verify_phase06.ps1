param(
    [Parameter(Mandatory=$true)][string]$CloudPython,
    [string]$Evidence = (Join-Path $env:LOCALAPPDATA 'CLYDEX/tmp/phase06-verification')
)
$ErrorActionPreference = 'Stop'
Set-Location (Split-Path -Parent $PSScriptRoot)
New-Item -ItemType Directory -Path $Evidence -Force | Out-Null
function Check-Exit([string]$Label) { if ($LASTEXITCODE -ne 0) { throw "$Label failed; see evidence." } }
python -m unittest discover -v *> (Join-Path $Evidence 'final-python.txt')
Check-Exit 'Desktop regression tests'
python -m ruff check --no-cache src tests *> (Join-Path $Evidence 'final-python-lint.txt')
Check-Exit 'Desktop lint'
& $CloudPython -m unittest discover -s cloud/tests -v *> (Join-Path $Evidence 'final-cloud.txt')
Check-Exit 'Cloud tests (simulated SQL repository)'
& $CloudPython -m ruff check cloud/src cloud/tests *> (Join-Path $Evidence 'final-cloud-lint.txt')
Check-Exit 'Cloud lint'
python -m compileall -q src tests scripts *> (Join-Path $Evidence 'final-compile.txt')
Check-Exit 'Python compilation'
& $CloudPython -m compileall -q cloud/src cloud/tests *> (Join-Path $Evidence 'final-cloud-compile.txt')
Check-Exit 'Cloud compilation'
Push-Location frontend
try {
    npm test *> (Join-Path $Evidence 'final-frontend.txt')
    Check-Exit 'Frontend tests'
    npm run build *> (Join-Path $Evidence 'final-build.txt')
    Check-Exit 'TypeScript and frontend build'
} finally { Pop-Location }
Push-Location v1-old
try {
    python -m unittest discover -v *> (Join-Path $Evidence 'final-archive.txt')
    Check-Exit 'Independent archive regression tests'
} finally { Pop-Location }
Write-Output 'Phase 06 local checks passed. This script does not establish native SQL, Linux deployment, audio, provider or production acceptance.'
