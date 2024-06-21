FROM python:3.9-slim

# Set the working directory inside the container
RUN mkdir /data
WORKDIR /app

# Install necessary packages
RUN apt-get update && apt-get install -y apt-transport-https
RUN apt-get install -y libtcmalloc-minimal4
RUN apt-get install -y sox
RUN apt-get install -y git

RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    software-properties-common \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Expose port 8501
EXPOSE 8501

# Copy all files from the same directory as the Dockerfile
WORKDIR /app
COPY . .