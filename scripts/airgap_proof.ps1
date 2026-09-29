param([string]$Image="ulpf-test")
docker run --rm --network none $Image python -m cli.main --help
Write-Output "air-gap proof complete"
