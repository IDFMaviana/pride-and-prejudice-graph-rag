# Python image
FROM python:3.12-slim

# work dir
WORKDIR /app

# optimize cache
COPY requirements.txt .

# dependencies
RUN pip install --no-cache-dir -r requirements.txt

#
COPY ./src /app/src

# execute
CMD ["python", "src/main.py"]