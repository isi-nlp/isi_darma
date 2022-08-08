#FROM nvidia/cuda:10.2-devel-ubuntu18.04
#FROM nvidia/cuda:11.1-devel-ubuntu20.04
FROM ubuntu:focal

# suppress prompts https://stackoverflow.com/a/67452950/1506477
ARG DEBIAN_FRONTEND=noninteractive
RUN apt update  && \
    apt install -y curl python3.9 python3-pip python3.9-dev \
        build-essential git locales locales-all nodejs npm \
    && apt-get autoremove --purge

ENV LC_ALL en_US.UTF-8
ENV LANG en_US.UTF-8
ENV LANGUAGE en_US.UTF-8


# Update pip
RUN  ln -s /usr/bin/python3.9 /usr/bin/python && python -m pip install --upgrade pip
RUN npm install -g heroku

#Make non-root user;
RUN useradd --create-home darma
#RUN chown -Rv rtguser:rtguser /home/rtguser

USER darma
# pip installed bins go here, they needs to be in PATH
RUN mkdir -p /home/darma/.local/bin /home/darma/work /home/darma/mephisto-data
#ENV CUDA_HOME="/usr/local/cuda/"
ENV PATH="/home/darma/.local/bin:${PATH}"

WORKDIR /home/darma/work

COPY --chown=darma:darma darma_chat ./darma_chat
COPY --chown=darma:darma setup.py ./
COPY --chown=darma:darma requirements.txt ./
COPY --chown=darma:darma MANIFEST.in ./
COPY --chown=darma:darma README.md ./

RUN pip install --user -e .  && pip cache purge
RUN mephisto config core.main_data_directory /home/darma/mephisto-data \
    && mephisto check

# Initialize heroku; hmmm... do this at runtime with user credentials
# RUN heroku login -i && python -m mephisto.scripts.heroku.initialize_heroku

CMD bash
