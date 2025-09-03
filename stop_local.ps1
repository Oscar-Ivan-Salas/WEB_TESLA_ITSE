# Detiene procesos en puertos 8000 y 8080
$ErrorActionPreference = 'SilentlyContinue'
function KillByPort($port) {
  $lines = netstat -ano | findstr LISTENING | findstr ":$port"
  foreach ($line in $lines) { $parts = $line -split "\s+"; $pid = $parts[-1]; if ($pid -match "^\d+$") { taskkill /PID $pid /F | Out-Null } }
}
KillByPort 8000
KillByPort 8080
Write-Host '🛑 Procesos locales detenidos.'
