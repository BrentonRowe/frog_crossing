param(
    [switch]$SkipBuild
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

Set-Location (Split-Path -Parent $MyInvocation.MyCommand.Path)

$python = "C:/Users/brent/AppData/Local/Microsoft/WindowsApps/python3.11.exe"

# Prevent packaging/publishing nested git metadata
$nestedGit = "tetris-web\.git"
$nestedGitHidden = "tetris-web\.git_hidden_pygbag"

if (-not $SkipBuild) {
    if (Test-Path $nestedGitHidden) {
        Remove-Item -Recurse -Force $nestedGitHidden
    }

    $restoreNestedGit = $false
    if (Test-Path $nestedGit) {
        Move-Item $nestedGit $nestedGitHidden
        $restoreNestedGit = $true
    }

    try {
        & $python -m pip install -U pygbag
        Remove-Item -Recurse -Force "build\web" -ErrorAction SilentlyContinue
        # pygbag starts a local dev server and blocks.
        # For publishing, we only need the build output; start it as a process and stop once files exist.
        $proc = Start-Process -FilePath $python -ArgumentList @('-m','pygbag','frog_crossing.py') -PassThru -NoNewWindow
        try {
            $deadline = (Get-Date).AddMinutes(5)
            while (-not (Test-Path "build\web\index.html") -and (Get-Date) -lt $deadline) {
                Start-Sleep -Milliseconds 250
            }
            if (-not (Test-Path "build\web\index.html")) {
                throw "pygbag build did not produce build\\web\\index.html within 5 minutes."
            }
        } finally {
            if ($null -ne $proc -and -not $proc.HasExited) {
                Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
            }
        }
    } finally {
        if ($restoreNestedGit -and (Test-Path $nestedGitHidden)) {
            Move-Item $nestedGitHidden $nestedGit
        }
    }
}

if (-not (Test-Path "build\web")) {
    throw "Missing build\\web output. Run pygbag first or omit -SkipBuild."
}

Remove-Item -Recurse -Force docs -ErrorAction SilentlyContinue
Copy-Item -Recurse -Force "build\web" "docs"

git add docs

# Commit only if there are staged changes
$hasStaged = $true
& git diff --cached --quiet
if ($LASTEXITCODE -eq 0) { $hasStaged = $false }

if ($hasStaged) {
    git commit -m "Publish web build (docs)"
}

git push

# Enable/Update GitHub Pages to serve from /docs on main
try {
    gh api -X POST "repos/BrentonRowe/frog_crossing/pages" -f "source[branch]=main" -f "source[path]=/docs" | Out-Null
} catch {
    gh api -X PUT "repos/BrentonRowe/frog_crossing/pages" -f "source[branch]=main" -f "source[path]=/docs" | Out-Null
}

Write-Host "Published. URL: https://BrentonRowe.github.io/frog_crossing/"
