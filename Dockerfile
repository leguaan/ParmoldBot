FROM python:3.9-alpine

# Set the working directory
WORKDIR /app

# Install SQLite and other dependencies
RUN apk add --no-cache gcc musl-dev python3-dev libffi-dev sqlite-dev

# Copy the requirements file into the container
COPY requirements.txt /app/

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY main.py /app/

# Command to run your bot
CMD ["python", "/app/main.py"]
