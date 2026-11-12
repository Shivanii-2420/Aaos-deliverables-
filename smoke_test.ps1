#!/usr/bin/env pwsh
# Smoke test script: Create agent -> version -> run -> evaluation case -> execute evaluation

$ErrorActionPreference = "Stop"

Write-Host "=== SMOKE TEST START ===" -ForegroundColor Green

# Step 1: Create Agent
Write-Host "`n[1/5] Creating agent..."
$agent = Invoke-RestMethod -Method Post `
  -Uri http://127.0.0.1:8000/agents `
  -Body (ConvertTo-Json @{ name="SmokeTestAgent"; owner="test"; description="Smoke test" }) `
  -ContentType "application/json"
$agentId = $agent.id
Write-Host "✓ Agent created with ID: $agentId"

# Step 2: Create Agent Version
Write-Host "`n[2/5] Creating agent version..."
$version = Invoke-RestMethod -Method Post `
  -Uri "http://127.0.0.1:8000/agents/$agentId/versions" `
  -Body (ConvertTo-Json @{ version="1.0"; model_name="azure/gpt-4o-mini" }) `
  -ContentType "application/json"
$versionId = $version.id
Write-Host "✓ Version created with ID: $versionId"

# Step 3: Create Test Run
Write-Host "`n[3/5] Creating test run..."
$run = Invoke-RestMethod -Method Post `
  -Uri "http://127.0.0.1:8000/versions/$versionId/runs" `
  -Body (ConvertTo-Json @{}) `
  -ContentType "application/json"
$runId = $run.id
Write-Host "✓ Test run created with ID: $runId"

# Step 4: Create Evaluation Case
Write-Host "`n[4/5] Creating evaluation case..."
$case = Invoke-RestMethod -Method Post `
  -Uri http://127.0.0.1:8000/evaluation-cases `
  -Body (ConvertTo-Json @{ name="Basic Test"; prompt="What is 2+2?"; expected_response="4"; category="MATH" }) `
  -ContentType "application/json"
$caseId = $case.id
Write-Host "✓ Evaluation case created with ID: $caseId"

# Step 5: Execute Evaluation
Write-Host "`n[5/5] Executing evaluation..."
try {
    $result = Invoke-RestMethod -Method Post `
      -Uri "http://127.0.0.1:8000/evaluation-execution/$runId" `
      -ContentType "application/json"
    Write-Host "✓ Evaluation executed successfully!"
    Write-Host "`nResult:`n$($result | ConvertTo-Json -Depth 2)"
    Write-Host "`n=== SMOKE TEST PASSED ===" -ForegroundColor Green
    exit 0
} catch {
    Write-Host "✗ Evaluation execution failed!" -ForegroundColor Red
    Write-Host "Error: $($_.Exception.Message)"
    Write-Host "`nFull error:`n$_"
    exit 1
}
