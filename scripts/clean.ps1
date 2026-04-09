# Remove caches and build artifacts (not .venv).
$RepoRoot = Split-Path -Parent $PSScriptRoot
Write-Host "Cleaning $RepoRoot ..."
Get-ChildItem $RepoRoot -Recurse -Filter "__pycache__" -Directory |
    Where-Object { $_.FullName -notlike "*\.venv\*" } |
    Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
Get-ChildItem $RepoRoot -Recurse -Include "*.pyc","*.pyo" |
    Where-Object { $_.FullName -notlike "*\.venv\*" } |
    Remove-Item -Force -ErrorAction SilentlyContinue
@(".pytest_cache", ".ruff_cache", ".mypy_cache") | ForEach-Object {
    $p = Join-Path $RepoRoot $_
    if (Test-Path $p) { Remove-Item $p -Recurse -Force }
}
Write-Host "✓ Clean complete."
