FROM python:3.10.3-slim-bullseye

# Update package lists
RUN apt-get update

# Core build and development tools
RUN apt-get install -y --no-install-recommends \
    gcc \
    build-essential \
    cmake \
    gfortran \
    musl-dev \
    python3-dev \
    libffi-dev

# Python and database libraries
RUN apt-get install -y --no-install-recommends \
    python3-numpy \
    sqlite3 \
    libsqlite3-dev

# Image processing and multimedia libraries
RUN apt-get install -y --no-install-recommends \
    graphicsmagick \
    libgraphicsmagick1-dev \
    libatlas-base-dev \
    libavcodec-dev \
    libavformat-dev \
    libgtk2.0-dev \
    libjpeg-dev \
    liblapack-dev \
    libswscale-dev

# Utility tools
RUN apt-get install -y --no-install-recommends \
    git \
    wget \
    curl \
    pkg-config \
    software-properties-common \
    zip

# Clean up apt cache to reduce image size
RUN apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Set the working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY *.py /app/

# Command to run the application
CMD ["python", "/app/main.py"]
