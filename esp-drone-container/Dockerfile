# Dockerfile

FROM espressif/idf:release-v4.4

ENV IDF_PATH=/opt/esp/idf
ENV HOME=/root
WORKDIR /project

RUN apt-get update && \
    apt-get install -y python3-pip && \
    rm -rf /var/lib/apt/lists/*
