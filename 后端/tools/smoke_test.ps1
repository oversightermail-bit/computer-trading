$ErrorActionPreference = 'Continue'
$jbr   = 'C:\Program Files\JetBrains\IntelliJ IDEA 2025.3.3\jbr'
$mvn   = 'C:\Program Files\JetBrains\IntelliJ IDEA 2025.3.3\plugins\maven\lib\maven3\bin\mvn.cmd'
# script lives in <backend>\tools -> parent is the backend project dir (ASCII-safe: no literal Chinese path)
$work  = Split-Path -Parent $PSScriptRoot
Set-Location $work
$env:JAVA_HOME = $jbr

function Say($t) { Write-Host ('### ' + $t) }

# ---------- 1. build ----------
Say 'BUILD'
& $mvn -B -DskipTests package 2>&1 | Select-Object -Last 20 | ForEach-Object { [string]$_ } | Write-Host
$jar = Join-Path $work 'target\hw-price-backend-1.0.0.jar'
if (-not (Test-Path $jar)) { Say 'BUILD FAILED - jar missing'; exit 1 }
Say 'BUILD OK'

# ---------- 2. start ----------
Say 'START APP'
$outLog = Join-Path $work 'target\app.log'
$errLog = Join-Path $work 'target\app-err.log'
Remove-Item $outLog, $errLog -ErrorAction SilentlyContinue
$proc = Start-Process -FilePath (Join-Path $jbr 'bin\java.exe') `
    -ArgumentList @('-jar', 'target\hw-price-backend-1.0.0.jar') `
    -WorkingDirectory $work -RedirectStandardOutput $outLog -RedirectStandardError $errLog `
    -PassThru -WindowStyle Hidden
$started = $false
for ($i = 0; $i -lt 90; $i++) {
    Start-Sleep -Seconds 1
    if ($proc.HasExited) { break }
    try {
        $r = Invoke-RestMethod -Uri 'http://127.0.0.1:8080/api/public/hardware' -TimeoutSec 3
        if ($r.code -eq 0) { $started = $true; break }
    } catch { }
}
if (-not $started) {
    Say 'APP START FAILED'
    Get-Content $outLog -Tail 60 -ErrorAction SilentlyContinue
    Get-Content $errLog -Tail 60 -ErrorAction SilentlyContinue
    if (-not $proc.HasExited) { Stop-Process -Id $proc.Id -Force }
    exit 1
}
Say 'APP STARTED'

function Show($title, $resp) {
    Write-Host ('  [' + $title + '] code=' + $resp.code + ' msg=' + $resp.message)
    $json = $resp | ConvertTo-Json -Depth 8 -Compress
    if ($json.Length -gt 500) { $json = $json.Substring(0, 500) + '...' }
    Write-Host ('    ' + $json)
}

try {
    # ---------- 3. public api ----------
    Say '3. PUBLIC API'
    $r = Invoke-RestMethod 'http://127.0.0.1:8080/api/public/hardware'
    Show ('hardware count=' + $r.data.Count) $r
    $r = Invoke-RestMethod 'http://127.0.0.1:8080/api/public/price/content?type=cpu'
    Show 'price/content cpu' $r
    $r = Invoke-RestMethod 'http://127.0.0.1:8080/api/public/price/series?type=gpu'
    Show ('price/series gpu series=' + $r.data.series.Count + ' dates=' + $r.data.dates.Count + ' recommend=' + $r.data.recommend.Count) $r
    $r = Invoke-RestMethod 'http://127.0.0.1:8080/api/public/search?keyword=4060'
    Show ('search 4060 hits=' + $r.data.products.Count) $r
    $r = Invoke-RestMethod 'http://127.0.0.1:8080/api/public/subscribe/plans'
    Show ('subscribe/plans count=' + $r.data.Count) $r

    # ---------- 4. reset demo user (make test repeatable) ----------
    Say '4. RESET DEMO USER'
    $mysql = 'C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe'
    $sql = "DELETE l FROM t_ai_quota_log l JOIN t_user u ON u.id = l.user_id WHERE u.username='demo'; " +
           "DELETE s FROM t_ai_session s JOIN t_user u ON u.id = s.user_id WHERE u.username='demo'; " +
           "DELETE sub FROM t_user_subscription sub JOIN t_user u ON u.id = sub.user_id WHERE u.username='demo'; " +
           "DELETE FROM t_user WHERE username='demo';"
    $sql | & $mysql -u root -p123456 --default-character-set=utf8mb4 hw_price 2>$null
    Write-Host '  demo user reset OK'

    # ---------- 5. register / login ----------
    Say '5. REGISTER / LOGIN'
    $body = @{ username = 'demo'; password = '123456' } | ConvertTo-Json
    try {
        $r = Invoke-RestMethod -Method Post 'http://127.0.0.1:8080/api/public/register' -ContentType 'application/json' -Body $body
        Show 'register' $r
    } catch {
        if ($_.ErrorDetails -and $_.ErrorDetails.Message) {
            $r = $_.ErrorDetails.Message | ConvertFrom-Json
        } else {
            $r = [pscustomobject]@{ code = '(unknown)'; message = 'register already exists (expected)' }
        }
        Show 'register(exists)' $r
    }
    $r = Invoke-RestMethod -Method Post 'http://127.0.0.1:8080/api/public/login' -ContentType 'application/json' -Body $body
    Show 'login' $r
    $token = $r.data.token
    $H = @{ Authorization = 'Bearer ' + $token }

    # ---------- 6. quota + ai (free plan 3/day) ----------
    Say '6. QUOTA + AI (free 3/day)'
    $r = Invoke-RestMethod 'http://127.0.0.1:8080/api/auth/quota' -Headers $H
    Show 'quota(free)' $r
    for ($i = 1; $i -le 4; $i++) {
        $body = @{ content = 'budget 5000 for gaming' } | ConvertTo-Json
        try {
            $r = Invoke-RestMethod -Method Post 'http://127.0.0.1:8080/api/auth/ai/chat' -Headers $H -ContentType 'application/json' -Body $body
            Show ('ai/chat #' + $i) $r
        } catch {
            $status = [int]$_.Exception.Response.StatusCode
            $r = $_.ErrorDetails.Message | ConvertFrom-Json
            Show ('ai/chat #' + $i + ' HTTP=' + $status) $r
            if ($status -ne 429 -or $r.code -ne 42901) { Say 'EXPECTED 429/42901 MISSING'; exit 2 }
        }
    }

    # ---------- 7. free plan image -> 403 ----------
    Say '7. FREE PLAN IMAGE -> 403'
    try {
        $body = @{ content = 'check this config list'; imageUrl = 'https://example.com/a.jpg' } | ConvertTo-Json
        Invoke-RestMethod -Method Post 'http://127.0.0.1:8080/api/auth/ai/chat' -Headers $H -ContentType 'application/json' -Body $body | Out-Null
        Say 'EXPECTED 403 MISSING'
        exit 2
    } catch {
        $status = [int]$_.Exception.Response.StatusCode
        $r = $_.ErrorDetails.Message | ConvertFrom-Json
        Show ('ai/chat image HTTP=' + $status) $r
        if ($status -ne 403) { Say 'EXPECTED 403 MISSING'; exit 2 }
    }

    # ---------- 8. upgrade to pro plan ----------
    Say '8. UPGRADE (planId=3)'
    $body = @{ planId = 3 } | ConvertTo-Json
    $r = Invoke-RestMethod -Method Post 'http://127.0.0.1:8080/api/auth/subscribe/order' -Headers $H -ContentType 'application/json' -Body $body
    Show 'subscribe/order' $r
    $r = Invoke-RestMethod 'http://127.0.0.1:8080/api/auth/subscribe/me' -Headers $H
    Show 'subscribe/me' $r
    $r = Invoke-RestMethod 'http://127.0.0.1:8080/api/auth/quota' -Headers $H
    Show 'quota(pro)' $r

    # ---------- 9. pro plan image (cost 2) ----------
    Say '9. PRO PLAN IMAGE (cost=2)'
    $body = @{ content = 'check this config list'; imageUrl = 'https://example.com/a.jpg' } | ConvertTo-Json
    $r = Invoke-RestMethod -Method Post 'http://127.0.0.1:8080/api/auth/ai/chat' -Headers $H -ContentType 'application/json' -Body $body
    Show 'ai/chat image' $r
    $r = Invoke-RestMethod 'http://127.0.0.1:8080/api/auth/quota/logs?page=1&size=5' -Headers $H
    Show ('quota/logs records=' + $r.data.records.Count) $r
    $r = Invoke-RestMethod 'http://127.0.0.1:8080/api/auth/quota' -Headers $H
    Show 'quota(after image cost=2)' $r

    Say 'SMOKE TEST ALL PASSED'
} finally {
    if (-not $proc.HasExited) { Stop-Process -Id $proc.Id -Force; Say 'APP STOPPED' }
}
