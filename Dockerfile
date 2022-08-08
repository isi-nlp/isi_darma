FROM python:3.9
RUN pip install --upgrade pip
RUN mkdir -p /isi_darma/isi_darma/
ADD ./src /isi_darma/isi_darma/src/
ADD ./requirements.txt /isi_darma/isi_darma/requirements.txt
RUN cd /isi_darma/isi_darma/src/
RUN pip install -r /isi_darma/isi_darma/requirements.txt
CMD ["python3", "/isi_darma/isi_darma/src/main.py"]