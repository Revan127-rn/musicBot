FROM python:3.11-slim-bookworm

# Çevre değişkenlerini ayarla
ENV PYTHONUNBUFFERED 1
ENV APP_HOME /app

# Sistem bağımlılıklarını kur (FFmpeg ve derleme araçları)
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ffmpeg \
        git \
        ca-certificates \
        openssl \
        build-essential \
        python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Çalışma dizinini oluştur
WORKDIR $APP_HOME

# Tüm dosyaları kopyala
COPY . $APP_HOME/

# Bağımlılıkları doğrudan pip ile kur (Daha güvenli ve hızlıdır)
RUN pip install --no-cache-dir .

# Botu başlat
CMD ["python", "src/main.py"]
