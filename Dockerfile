FROM python:3.9-alpine
COPY requirements.txt /app/
COPY main.py /app/
RUN pip install -r /app/requirements.txt
ENTRYPOINT python /app/main.py
