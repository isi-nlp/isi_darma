#!/bin/sh

docker build -t isi_darma:latest .
echo "Build complete for isi_darma Docker image."
docker run -i --rm -dp 6060:6060 -v /isi_darma/docker_logs/:/logs/ isi_darma:latest