param(
	[string]$Jdk = 'C:\Program Files\Java\jdk-23',
	[string]$GhidraRoot = '',
	[string]$Rom = '',
	[ValidateSet('TraceGimmickLoader', 'TraceGimmickCalculations', 'TraceGimmickBattle')]
	[string]$Script = 'TraceGimmickLoader'
)
$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '../../..')).Path
if (!$GhidraRoot) { $GhidraRoot = Join-Path $repo 'Ghidra' }
if (!$Rom) { $Rom = Join-Path $repo 'Tomato Adventure (Japan).gba' }
$Rom = (Resolve-Path -LiteralPath $Rom).Path
$expected = '0d44380a3eed065b6ca0992d80a248ab001b978e925f7687d5dfcf1ae70e5c12'
$before = Get-FileHash -LiteralPath $Rom -Algorithm SHA256
if ($before.Hash.ToLowerInvariant() -ne $expected) { throw 'Input does not match the documented Japanese ROM SHA-256.' }
$protectedPaths = @($Rom)
$english = Join-Path $repo 'Tomato Adventure (Japan) (patched).gba'
if ((Test-Path -LiteralPath $english) -and $english -ne $Rom) { $protectedPaths += $english }
$protected = @($protectedPaths | ForEach-Object {
	$item = Get-Item -LiteralPath $_
	[PSCustomObject]@{ Path = $item.FullName; SHA256 = (Get-FileHash -LiteralPath $_ -Algorithm SHA256).Hash; Size = $item.Length; LastWriteTimeUtc = $item.LastWriteTimeUtc }
})
$run = Join-Path $repo ('reverse_engineering/ghidra/run-' + [Guid]::NewGuid().ToString('N'))
foreach ($dir in @('projects','settings','cache','tmp','home','classes')) {
	New-Item -ItemType Directory -Path (Join-Path $run $dir) -Force | Out-Null
}
$protected | ConvertTo-Json | Set-Content (Join-Path $run 'input-metadata.json') -Encoding UTF8
Write-Output "Compiling isolated script in: $run"
# Standard JavaFileManager reads dependency classes with JarFile, avoiding the
# observed ZipFS and directory case-check failures. No dependency copies needed.
& (Join-Path $Jdk 'bin/java.exe') (Join-Path $PSScriptRoot 'CompileScript.java') $GhidraRoot (Join-Path $PSScriptRoot ($Script + '.java')) (Join-Path $run 'classes')
if ($LASTEXITCODE -ne 0) { throw 'Ghidra script compilation failed.' }
$postScriptArgs = @('-postScript', ($Script + '.class'), (Join-Path $run 'loader.txt'))
if ($Script -in @('TraceGimmickCalculations', 'TraceGimmickBattle')) { $postScriptArgs += $english }
# Equivalent Java entry point to support/analyzeHeadless.bat. Bypass LaunchSupport's
# -save (writes per-user JDK selection); no installation or global settings edits.
$javaArgs = @('-Xmx2G','-Xshare:off','-Djava.system.class.loader=ghidra.GhidraClassLoader',
	'-Dfile.encoding=UTF8','-Duser.language=en','-Duser.country=US','--enable-native-access=ALL-UNNAMED',
	('-Duser.home=' + (Join-Path $run 'home')),
	('-Dapplication.settingsdir=' + (Join-Path $run 'settings')),
	('-Dapplication.cachedir=' + (Join-Path $run 'cache')),
	('-Dapplication.tempdir=' + (Join-Path $run 'tmp')),
	('-Djava.io.tmpdir=' + (Join-Path $run 'tmp')),
	'-cp',(Join-Path $GhidraRoot 'Ghidra/Framework/Utility/lib/Utility.jar'),
	'ghidra.Ghidra','ghidra.app.util.headless.AnalyzeHeadless',
	(Join-Path $run 'projects'),'loader','-import',$Rom,
	'-loader','BinaryLoader','-loader-baseAddr','0x08000000','-loader-fileOffset','0',
	'-processor','ARM:LE:32:v4t','-cspec','default','-noanalysis','-readOnly',
	'-scriptPath',(Join-Path $run 'classes')) + $postScriptArgs + @(
	'-log',(Join-Path $run 'headless.log'),'-scriptlog',(Join-Path $run 'script.log'))
$javaArgs | ConvertTo-Json | Set-Content (Join-Path $run 'arguments.json') -Encoding UTF8
Write-Output "Analysis directory: $run"
try {
	& (Join-Path $Jdk 'bin/java.exe') @javaArgs
	if ($LASTEXITCODE -ne 0) { throw "Ghidra exited with code $LASTEXITCODE" }
	if (!(Test-Path (Join-Path $run 'loader.txt'))) { throw 'Expected script output was not produced; inspect logs.' }
	if ((Get-Content (Join-Path $run 'loader.txt') -Tail 1) -ne 'TRACE_COMPLETE') { throw 'Analysis script did not finish; inspect logs.' }
	if (Select-String -Path (Join-Path $run 'headless.log') -Pattern 'REPORT SCRIPT ERROR|ERROR Unexpected' -Quiet) { throw 'Ghidra reported a script error.' }
} finally {
	foreach ($record in $protected) {
		$item = Get-Item -LiteralPath $record.Path
		$after = Get-FileHash -LiteralPath $record.Path -Algorithm SHA256
		if ($after.Hash -ne $record.SHA256 -or $item.Length -ne $record.Size -or $item.LastWriteTimeUtc -ne $record.LastWriteTimeUtc) { throw "Protected ROM changed during analysis: $($record.Path)" }
	}
}
Write-Output "Completed: $run"
