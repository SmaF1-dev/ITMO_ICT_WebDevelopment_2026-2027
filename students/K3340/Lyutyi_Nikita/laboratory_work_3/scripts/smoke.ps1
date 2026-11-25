param(
    [string]$Base = 'http://127.0.0.1:8000',
    [string]$Username = 'admin'
)

$ErrorActionPreference = 'Stop'
$cred = Get-Credential -UserName $Username -Message 'Суперпользователь ЛР3'
$body = @{ username = $cred.UserName; password = $cred.GetNetworkCredential().Password } | ConvertTo-Json
$login = Invoke-RestMethod -Method POST -Uri "$Base/auth/token/login/" -ContentType 'application/json' -Body $body
if (-not $login.auth_token) { throw 'Djoser не вернул auth_token' }
$headers = @{ Authorization = "Token $($login.auth_token)"; Accept = "application/json" }

$paths = @(
    '/auth/users/me/', '/api/advertisers/', '/api/employees/', '/api/categories/',
    '/api/services/', '/api/materials/', '/api/material-norms/', '/api/requests/',
    '/api/works/', '/api/contracts/', '/api/payment-orders/',
    '/api/reports/completed-works/', '/api/reports/payment-orders/',
    '/api/reports/services/', '/api/reports/advertiser-requests/',
    '/api/reports/employee-workload/', '/api/reports/quarterly/'
)
foreach ($path in $paths) {
    $null = Invoke-RestMethod -Uri "$Base$path" -Headers $headers
    Write-Host "PASS GET $path" -ForegroundColor Green
}

$ads = Invoke-RestMethod -Uri "$Base/api/advertisers/" -Headers $headers
if ($ads.results.Count -gt 0) {
    $id = $ads.results[0].id
    $obj = Invoke-RestMethod -Uri "$Base/api/advertisers/$id/" -Headers $headers
    if ($null -eq $obj.requests) { throw 'Нет вложенных заявок в advertiser detail' }
    Write-Host "PASS nested 1:N advertiser=$id" -ForegroundColor Green
}
$services = Invoke-RestMethod -Uri "$Base/api/services/" -Headers $headers
if ($services.results.Count -gt 0) {
    $foundMaterial = $false
    foreach ($service in $services.results) {
        $id = $service.id
        $obj = Invoke-RestMethod -Uri "$Base/api/services/$id/" -Headers $headers
        if ($null -eq $obj.materials) { throw 'Нет вложенных материалов в service detail' }
        if ($obj.materials.Count -gt 0) {
            $foundMaterial = $true
            Write-Host "PASS nested M:N service=$id; materials=$($obj.materials.Count)" -ForegroundColor Green
            break
        }
    }
    if (-not $foundMaterial) { throw 'В демоданных нет услуги с материалами для показа связи M:N' }
}

# Explicit charset is necessary for Russian text in Windows PowerShell 5.1.
$response = Invoke-WebRequest -Uri "$Base/api/reports/services/" -Headers $headers -UseBasicParsing
if ($response.Headers['Content-Type'] -notmatch 'charset=utf-8') {
    throw 'В JSON не указан charset=utf-8'
}
Write-Host 'PASS JSON charset=utf-8' -ForegroundColor Green

# Documentation should be accessible without an authentication token.
foreach ($path in @('/api/schema/', '/api/docs/')) {
    $response = Invoke-WebRequest -Uri "$Base$path" -UseBasicParsing
    if ($response.StatusCode -ne 200) { throw "HTTP $($response.StatusCode) for $path" }
    Write-Host "PASS GET $path" -ForegroundColor Green
}
Write-Host 'Все smoke-проверки API завершились успешно.' -ForegroundColor Green
