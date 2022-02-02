#!/bin/sh

conda activate darma
#python3 /isi_darma/isi_darma/src/basic_bot.py &
python3 src/basic_bot.py > darma_logs.txt &
