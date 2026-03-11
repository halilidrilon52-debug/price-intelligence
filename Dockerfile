# Simple Dockerfile for Price Intelligence Flask app
FROM python:3.12-slim

# set workdir
WORKDIR /app

# copy requirements and install
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# copy app code
COPY . /app

# expose port
EXPOSE 5001

CMD ["python", "app.py"]
