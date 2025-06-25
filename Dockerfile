# syntax=docker/dockerfile:1.4
FROM python:3.11.9-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

ARG PLATFORM_COMMON_TOKEN
ENV PLATFORM_COMMON_TOKEN=${PLATFORM_COMMON_TOKEN}

# Copy the template requirements file
COPY requirements.txt.template .

# Substitute the token placeholder in the template to create the actual requirements.txt
RUN sed "s|\${PLATFORM_COMMON_TOKEN}|${PLATFORM_COMMON_TOKEN}|g" requirements.txt.template > requirements.txt

RUN pip install --upgrade pip && \
    pip install -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
