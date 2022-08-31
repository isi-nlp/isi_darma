#!/bin/sh

docker run -i --rm -dP -v /isi_darma/docker_logs/:/logs/ --name $1 isi_darma:latest && docker logs -f $1