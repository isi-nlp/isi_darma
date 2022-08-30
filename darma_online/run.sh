#!/bin/sh

docker run -i --rm -dP -v /isi_darma/docker_logs/:/logs/ -v /isi_darma/isi_darma/darma_online/src/darma_online/data:/isi_darma/isi_darma/darma_online/src/darma_online/data/conversations --name $1 isi_darma:latest && docker logs -f $1