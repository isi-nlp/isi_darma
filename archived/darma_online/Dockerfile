FROM python:3.9
RUN pip install --upgrade pip
RUN mkdir -p /isi_darma/isi_darma/darma_online/
ADD ./src /isi_darma/isi_darma/darma_online/src/
ADD ./requirements.txt /isi_darma/isi_darma/darma_online/requirements.txt
RUN cd /isi_darma/isi_darma/darma_online/ && pip install -r requirements.txt
CMD ["python3", "/isi_darma/isi_darma/darma_online/src/main.py", "-p", "-s", "france", "-l", "french"]