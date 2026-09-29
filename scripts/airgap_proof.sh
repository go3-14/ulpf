#!/usr/bin/env sh
set -eu
IMAGE=${1:-ulpf-test}
echo "processing with network disabled"
docker run --rm --network none "$IMAGE" python -m cli.main --help
echo "air-gap proof complete"
