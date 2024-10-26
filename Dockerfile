FROM hdgigante/python-opencv:4.10.0-debian

RUN apt-get update && apt-get install -y python3-pip

WORKDIR /app

COPY requirements.txt .

RUN pip3 install --no-cache-dir --break-system-packages -r requirements.txt

COPY *.py .

CMD ["python3", "main.py"]
