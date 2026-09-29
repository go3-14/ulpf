param([string]$Version="dev")
New-Item -ItemType Directory -Force dist/wheelhouse | Out-Null
docker build --target runtime -t "ulpf:$Version" .
docker save "ulpf:$Version" | gzip > "dist/ulpf-$Version.tar.gz"
Get-FileHash "dist/ulpf-$Version.tar.gz"
python -m pip download -r requirements.txt -d dist/wheelhouse
