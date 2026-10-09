# Outer wrapper only. No optimization unless -Execute is supplied.
[CmdletBinding()]
param(
    [string]$Python = "python",
    [string]$Instance = "all",
    [string]$RunGroup = "all",
    [string]$OutputRoot = "outputs",
    [ValidateSet("strict", "numerical")][string]$IdentityMode = "strict",
    [switch]$Execute,
    [switch]$ShowCommands,
    [switch]$CheckEnvironment
)
$ErrorActionPreference = "Stop"
$Launcher = Join-Path $PSScriptRoot "run_experiments.py"
$LaunchArgs = @($Launcher, "--study", "3d", "--instance", $Instance, "--run-group", $RunGroup, "--output-root", $OutputRoot, "--identity-mode", $IdentityMode)
if ($Execute) { $LaunchArgs += "--execute" }
if ($ShowCommands) { $LaunchArgs += "--show-commands" }
if ($CheckEnvironment) { $LaunchArgs += "--check-environment" }
& $Python @LaunchArgs
if ($LASTEXITCODE -ne 0) { throw "Recorded experiment launcher failed (exit code $LASTEXITCODE)." }
