FROM python:3.11-slim-bookworm

ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1
ENV APP_HOME /app
ENV PYTHONPATH $APP_HOME

RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg git ca-certificates openssl build-essential python3-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR $APP_HOME

# Önce sadece requirements.txt kopyalayalım (cache avantajı için )
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Sonra tüm projeyi kopyalayalım
COPY . .

# Botu başlat
CMD ["python", "-m", "src.main"]
