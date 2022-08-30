#!/bin/sh

git fetch && git pull
docker build -t darma_online:$1 .
echo "Build complete for isi_darma Docker image."