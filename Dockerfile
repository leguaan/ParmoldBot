FROM hdgigante/python-opencv:4.10.0-debian@sha256:6f31c2e90b4467a405c13490423962627bbcfddf14b208e6a75eb359739b7f71

RUN apt-get update && apt-get install -y python3-pip

WORKDIR /app

COPY requirements.txt .

RUN pip3 install --no-cache-dir --break-system-packages -r requirements.txt

COPY *.py .

CMD ["python3", "main.py"]
