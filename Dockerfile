FROM python:3.11-slim-bookworm

ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1
ENV APP_HOME /app
# Python'un src klasörünü bulabilmesi için yolu ekliyoruz
ENV PYTHONPATH $APP_HOMEFROM python:3.11-slim-bookworm

# Çevre değişkenleri
ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1
ENV APP_HOME /app
# Çalışma dizinini Python yoluna ekle
ENV PYTHONPATH $APP_HOME

# Sistem bağımlılıkları
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg git ca-certificates openssl build-essential python3-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR $APP_HOME

# Dosyaları kopyala
COPY . $APP_HOME/

# Bağımlılıkları kur
RUN pip install --no-cache-dir .

# KRİTİK DEĞİŞİKLİK: Botu modül olarak başlat (-m kullanıyoruz ve .py yazmıyoruz)
CMD ["python", "-m", "src.main"]


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
