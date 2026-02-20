# Add Claude to user PATH so it works in Cursor's terminal
# Run this once in PowerShell where "claude" already works (e.g. Windows PowerShell from Start menu)

$ErrorActionPreference = 'Stop'

Write-Host "Resolving 'claude'..." -ForegroundColor Cyan
$claudeCmd = Get-Command claude -ErrorAction SilentlyContinue
if (-not $claudeCmd) {
    Write-Host "ERROR: 'claude' is not in your PATH in this session. Run this script from a PowerShell window where typing 'claude' works." -ForegroundColor Red
    exit 1
}

$targetPath = $null
switch ($claudeCmd.CommandType) {
    'Application' { $targetPath = Split-Path $claudeCmd.Source -Parent }
    'Alias'       {
        $resolved = $claudeCmd.ResolvedCommandName
        if ($resolved) {
            $targetPath = Split-Path (Get-Command $resolved).Source -Parent
        }
    }
    default       { $targetPath = Split-Path $claudeCmd.Source -Parent }
}

if (-not $targetPath) {
    Write-Host "Could not get folder for claude. Command type: $($claudeCmd.CommandType)" -ForegroundColor Red
    exit 1
}

$currentUserPath = [Environment]::GetEnvironmentVariable('Path', 'User')
if ($currentUserPath -split ';' -contains $targetPath) {
    Write-Host "Claude's folder is already in your user PATH: $targetPath" -ForegroundColor Green
    Write-Host "If Cursor still can't run 'claude', fully quit Cursor and open it again." -ForegroundColor Yellow
    exit 0
}

$newPath = if ($currentUserPath) { "$currentUserPath;$targetPath" } else { $targetPath }
[Environment]::SetEnvironmentVariable('Path', $newPath, 'User')
Write-Host "Added to user PATH: $targetPath" -ForegroundColor Green
Write-Host "Fully quit Cursor and open it again, then try 'claude' in the terminal." -ForegroundColor Yellow
