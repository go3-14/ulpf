#!/usr/bin/env sh
set -eu
VERSION=${1:-dev}
mkdir -p dist/wheelhouse
docker build --target runtime -t "ulpf:${VERSION}" .
docker save "ulpf:${VERSION}" | gzip > "dist/ulpf-${VERSION}.tar.gz"
sha256sum "dist/ulpf-${VERSION}.tar.gz"
python -m pip download -r requirements.txt -d dist/wheelhouse
