#!/bin/sh

docker build -t isi_darma:latest .
echo "Build complete for isi_darma Docker image."
docker run -it --rm -p 8080:8080 -v ./:/isi_darma/src/logs/ isi_darma:latest