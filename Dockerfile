FROM python:3.10.3-slim-bullseye

RUN apt-get -y update
RUN apt-get install -y --fix-missing \
    gcc \
    musl-dev \
    python3-dev \
    libffi-dev \
    sqlite3 \
    libsqlite3-dev \
    build-essential \
    cmake \
    gfortran \
    git \
    wget \
    curl \
    graphicsmagick \
    libgraphicsmagick1-dev \
    libatlas-base-dev \
    libavcodec-dev \
    libavformat-dev \
    libgtk2.0-dev \
    libjpeg-dev \
    liblapack-dev \
    libswscale-dev \
    pkg-config \
    python3-dev \
    python3-numpy \
    software-properties-common \
    zip \
    && apt-get clean && rm -rf /tmp/* /var/tmp/*

WORKDIR /app
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt
COPY *.py /app/
CMD ["python", "/app/main.py"]
