<#
PowerShell helper script to POST FHIR AuditEvent to /fhir/notify, check response,
validate logs/alerts.log, run negative test, and run a small batch loop.

Usage examples (copy-paste ready):

# Single normal event and check last log line
.\tests\send_fhir_tests.ps1 -FilePath .\tests\sample_audit.json -Uri http://localhost:5001/fhir/notify

# Negative test (attack)
.\tests\send_fhir_tests.ps1 -FilePath .\tests\sample_audit_attack.json -Uri http://localhost:5001/fhir/notify

# Batch test: 50 events
.\tests\send_fhir_tests.ps1 -FilePath .\tests\sample_audit.json -Uri http://localhost:5001/fhir/notify -Count 50
#>
param(
  [Parameter(Mandatory=$true)] [string] $FilePath,
  [Parameter(Mandatory=$true)] [string] $Uri,
  [int] $Count = 1,
  [int] $DelayMs = 200
)

function Send-FhirEvent {
  param($File, $Uri)
  Write-Host "POST -> $Uri (file: $File)"
  try {
    $resp = Invoke-WebRequest -Uri $Uri -Method Post -ContentType "application/fhir+json" -InFile $File -ErrorAction Stop
    Write-Host "StatusCode: $($resp.StatusCode)"
    $content = $resp.Content
    try {
      $json = $content | ConvertFrom-Json
      Write-Host "Response JSON:" -ForegroundColor Cyan
      $json | ConvertTo-Json -Depth 10
      return $json
    } catch {
      Write-Host "Response (raw):" -ForegroundColor Yellow
      Write-Host $content
      return $null
    }
  } catch {
    Write-Host "Request failed:" -ForegroundColor Red
    Write-Host $_.Exception.Message
    return $null
  }
}

function Show-LastAlerts {
  param([int] $Tail = 5)
  $log = Join-Path -Path (Get-Location) -ChildPath "logs\alerts.log"
  if (-Not (Test-Path $log)) {
    Write-Host "alerts.log not found at $log" -ForegroundColor Red
    return
  }
  Write-Host "\n--- Last $Tail lines of logs/alerts.log ---" -ForegroundColor Green
  $lines = Get-Content -Path $log -Tail $Tail
  $i = 0
  foreach ($line in $lines) {
    $i++
    Write-Host "[$i] $line"
    try { $obj = $line | ConvertFrom-Json; $obj | ConvertTo-Json -Depth 8 } catch { }
  }
}

# Main
for ($i = 1; $i -le $Count; $i++) {
  $res = Send-FhirEvent -File $FilePath -Uri $Uri
  Start-Sleep -Milliseconds $DelayMs
}

# Show last 5 alerts and try to surface 8-class fields if present
Show-LastAlerts -Tail 8

# Quick grep for common 8-class fields
$logpath = Join-Path -Path (Get-Location) -ChildPath "logs\alerts.log"
if (Test-Path $logpath) {
  $last = Get-Content -Path $logpath -Tail 1
  try {
    $obj = $last | ConvertFrom-Json
    if ($obj.predicted_class) { Write-Host "predicted_class:"; $obj.predicted_class }
    if ($obj.class) { Write-Host "class:"; $obj.class }
    if ($obj.class_probs) { Write-Host "class_probs:"; $obj.class_probs | ConvertTo-Json -Depth 6 }
    if ($obj.classes) { Write-Host "classes:"; $obj.classes | ConvertTo-Json -Depth 6 }
  } catch { }
}
