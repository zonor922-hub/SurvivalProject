param(
    [Parameter(Mandatory=$true)][string]$EngineRoot,
    [string]$OutputDirectory,
    [ValidateRange(30,1800)][int]$TimeoutSeconds=900,
    [switch]$SkipSwimming,
    [switch]$InjectFailureForRunnerTest,
    [switch]$IncludeA10
)
$ErrorActionPreference='Stop'
$projectRoot=(Resolve-Path (Join-Path $PSScriptRoot '../../..')).Path
if (-not $OutputDirectory) {$OutputDirectory=Join-Path $projectRoot ('Saved/Verification/F01F02/'+(Get-Date -Format 'yyyyMMdd_HHmmss'))}
$null=New-Item -ItemType Directory -Path $OutputDirectory -Force
$OutputDirectory=(Resolve-Path -LiteralPath $OutputDirectory).Path
if ((Test-Path -LiteralPath (Join-Path $OutputDirectory 'context.json')) -or (Test-Path -LiteralPath (Join-Path $OutputDirectory 'summary.json'))) {throw 'Choose an unused output directory; existing evidence will not be overwritten'}
$editor=Join-Path $EngineRoot 'Engine/Binaries/Win64/UnrealEditor-Cmd.exe'
if (-not (Test-Path -LiteralPath $editor)) {throw "UnrealEditor-Cmd.exe not found: $editor"}
function SourceHashes {
    $hashes=@{}
    foreach ($folder in @('Content','Config')) {
        Get-ChildItem -LiteralPath (Join-Path $projectRoot $folder) -Recurse -File | ForEach-Object {
            $hashes[$_.FullName.Substring($projectRoot.Length+1)]=(Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash
        }
    }
    $hashes['SurvivalProject.uproject']=(Get-FileHash -LiteralPath (Join-Path $projectRoot 'SurvivalProject.uproject') -Algorithm SHA256).Hash
    return $hashes
}
$before=SourceHashes
$before | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $OutputDirectory 'source_hashes.json') -Encoding utf8
$sha=(& git -C $projectRoot rev-parse HEAD).Trim()
if ($LASTEXITCODE -ne 0) {throw 'Unable to identify tested commit'}
$dirty=@(& git -C $projectRoot status --porcelain=v1)
if ($LASTEXITCODE -ne 0) {throw 'Unable to inspect tested working tree'}
$context=[ordered]@{commit=$sha;working_tree=$dirty;project_root=$projectRoot;source=$PSScriptRoot;output=$OutputDirectory;skip_swimming=[bool]$SkipSwimming;inject_failure=[bool]$InjectFailureForRunnerTest;include_a10=[bool]$IncludeA10;started_utc=(Get-Date).ToUniversalTime().ToString('o')}
$contextPath=Join-Path $OutputDirectory 'context.json'
$context | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $contextPath -Encoding utf8
$bootstrap=Join-Path $OutputDirectory 'bootstrap.py'
$contextLiteral=ConvertTo-Json -InputObject $contextPath -Compress
@"
import os,runpy
os.environ['SURVIVAL_TEST_CONTEXT']=$contextLiteral
import json
with open($contextLiteral,encoding='utf-8-sig') as f: context=json.load(f)
runpy.run_path(os.path.join(context['source'],'f01_f02_runner.py'),run_name='__main__')
"@ | Set-Content -LiteralPath $bootstrap -Encoding utf8
$arguments=@(('"'+(Join-Path $projectRoot 'SurvivalProject.uproject')+'"'),('"-ExecutePythonScript='+$bootstrap+'"'),'-EnablePlugins=PythonScriptPlugin','-unattended','-nullrhi','-nosplash','-ddc=InstalledNoZenLocalFallback',('"-abslog='+(Join-Path $OutputDirectory 'Unreal.log')+'"'))
$process=Start-Process -FilePath $editor -ArgumentList $arguments -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $OutputDirectory 'stdout.log') -RedirectStandardError (Join-Path $OutputDirectory 'stderr.log')
$timedOut=-not $process.WaitForExit($TimeoutSeconds*1000)
if ($timedOut) {Stop-Process -Id $process.Id; $process.WaitForExit()}
$process.Refresh()
$after=SourceHashes
$changed=@(@($before.Keys)+@($after.Keys) | Sort-Object -Unique | Where-Object {$before[$_] -ne $after[$_]})
$summaryPath=Join-Path $OutputDirectory 'summary.json'
if (Test-Path -LiteralPath $summaryPath) {$summary=Get-Content -LiteralPath $summaryPath -Raw | ConvertFrom-Json}
else {$summary=[pscustomobject]@{passed=$false;error='Runner did not produce summary.json'}}
$summary | Add-Member -Force -NotePropertyName process_exit_code -NotePropertyValue $process.ExitCode
$summary | Add-Member -Force -NotePropertyName timed_out -NotePropertyValue $timedOut
$summary | Add-Member -Force -NotePropertyName changed_source_files -NotePropertyValue $changed
$ok=$summary.passed -and -not $timedOut -and $process.ExitCode -eq 0 -and $changed.Count -eq 0
$summary.passed=[bool]$ok
$summary | ConvertTo-Json -Depth 30 | Set-Content -LiteralPath $summaryPath -Encoding utf8
Write-Output "Results: $OutputDirectory"
Write-Output "Passed: $ok; editor exit: $($process.ExitCode); changed source files: $($changed.Count)"
if ($ok) {exit 0} else {exit 1}
