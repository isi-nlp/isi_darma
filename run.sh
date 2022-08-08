#!/bin/sh

docker run -i --rm -dP -v /isi_darma/docker_logs/:/logs/ --name darma isi_darma:latest && docker logs -f darma