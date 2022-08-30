#!/bin/sh

git fetch && git pull
docker build -t darma_online:latest .
echo "Build complete for isi_darma Docker image."