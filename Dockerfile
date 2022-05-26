FROM python:3.9
RUN mkdir /isi_darma/
ADD ./src /isi_darma/src/
ADD ./requirements.txt /isi_darma/requirements.txt
RUN cd /isi_darma/src/
RUN pip3 install -r requirements.txt
CMD ["python3", "src/main.py"]
