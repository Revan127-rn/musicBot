FROM python:3.11-slim-bookworm

ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1
ENV APP_HOME /app
# Python'un src klasörünü bulabilmesi için yolu ekliyoruz
ENV PYTHONPATH $APP_HOME

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ffmpeg \
        git \
        ca-certificates \
        openssl \
        build-essential \
        python3-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR $APP_HOME

COPY . $APP_HOME/

RUN pip install --no-cache-dir .

# Modül olarak başlatıyoruz
CMD ["python", "src/main.py"]
