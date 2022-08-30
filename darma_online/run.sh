#!/bin/sh

docker run -i --rm -dP -v /isi_darma/docker_logs/: /isi_darma/isi_darma/darma_online/src/logs/ --name $1 isi_darma:latest && docker logs -f $1