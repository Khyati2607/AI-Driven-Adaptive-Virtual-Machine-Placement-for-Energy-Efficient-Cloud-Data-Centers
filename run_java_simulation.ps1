# Run CloudSim Plus simulation using the Maven copy in this repo and JDK 17.
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$env:JAVA_HOME = "C:\Program Files\Java\jdk-17"
$env:Path = "$env:JAVA_HOME\bin;" + $env:Path
$mvn = Join-Path $root "apache-maven-3.9.16\bin\mvn.cmd"
if (-not (Test-Path $mvn)) {
    throw "Maven not found at $mvn"
}
Set-Location (Join-Path $root "cloudsim-simulation")
& $mvn test
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
& $mvn exec:java "-Dexec.args=../config/simulation_config.json"
exit $LASTEXITCODE
