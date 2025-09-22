# Use a lightweight Python base image
FROM python:3.11.9-slim

# Set the working directory inside the container
WORKDIR /app

# Set environment variables for non-buffered output and no.pyc files
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Copy the requirements file and install Python dependencies
COPY ./requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . /app