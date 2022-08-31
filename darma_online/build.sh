#!/bin/sh

git fetch && git pull
docker build -t isi_darma:latest .
echo "Build complete for isi_darma Docker image."