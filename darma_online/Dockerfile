FROM python:3.9
RUN pip install --upgrade pip
RUN mkdir -p /darma_online/darma_online/
ADD ./src /isi_darma/isi_darma/src/
ADD ./requirements.txt /isi_darma/isi_darma/requirements.txt
RUN cd /darma_online/darma_online/src/
RUN pip install -r /darma_online/darma_online/requirements.txt
CMD ["python3", "/isi_darma/isi_darma/src/main.py"]