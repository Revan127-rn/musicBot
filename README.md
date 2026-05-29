# Telegram Müzik Botu

Modern, gelişmiş ve yapay zeka destekli bir Telegram müzik botu projesi.

## Özellikler

*   YouTube üzerinden müzik arama ve indirme (MP3 formatında)
*   Kişisel çalma listeleri oluşturma ve yönetme
*   Şarkıları beğenme ve beğenilen şarkıları görüntüleme
*   Groq AI destekli kişiselleştirilmiş müzik önerileri
*   Telegram limitlerine uygun optimize edilmiş ses dosyaları
*   Yönetici (Admin) paneli ve bot istatistikleri
*   Redis ile önbellekleme
*   PostgreSQL veritabanı ve SQLAlchemy ORM
*   Docker ve Railway ile kolay dağıtım

## Teknolojiler

*   **Bot Framework:** `aiogram` (Python)
*   **Veritabanı:** `PostgreSQL`
*   **ORM:** `SQLAlchemy`
*   **Önbellekleme:** `Redis`
*   **YouTube Entegrasyonu:** `yt-dlp`
*   **Ses İşleme:** `FFmpeg`
*   **Yapay Zeka:** `Groq AI API`
*   **Dağıtım:** `Docker`, `Railway`, `GitHub Actions`

## Kurulum Rehberi

### 1. Ön Gereksinimler

*   Python 3.11+
*   Docker (isteğe bağlı, Railway deploy için)
*   PostgreSQL veritabanı erişimi
*   Redis sunucusu erişimi
*   Telegram Bot API Token
*   Groq AI API Key
*   GitHub hesabı ve bir repository

### 2. Ortam Değişkenleri ve GitHub Secrets

Bu proje, hassas bilgileri `.env` dosyası yerine **GitHub Secrets** kullanarak yönetmenizi önerir. `.env.example` dosyasını referans alarak, aşağıdaki değişkenleri GitHub repository'nizin `Settings -> Secrets and variables -> Actions` bölümüne eklemelisiniz:

*   **`BOT_TOKEN`**: [BotFather](https://t.me/BotFather) üzerinden alacağınız Telegram bot tokeni.
*   **`DATABASE_URL`**: PostgreSQL veritabanınızın bağlantı URL'si. Örnek: `postgresql+asyncpg://user:password@host:port/database_name`
*   **`REDIS_URL`**: Redis sunucunuzun bağlantı URL'si. Örnek: `redis://localhost:6379/0`
*   **`GROQ_API_KEY`**: [Groq Platformu](https://groq.com/) üzerinden alacağınız API anahtarı.
*   **`ADMIN_TELEGRAM_IDS`**: Botun yönetici özelliklerini kullanabilecek Telegram kullanıcı ID'leri. Birden fazla ID virgülle ayrılabilir (örneğin: `123456789,987654321`).
*   **`YTDLP_CACHE_DIR`**: (Opsiyonel) `yt-dlp` önbellek dizini. Varsayılan: `./.ytdlp_cache`
*   **`YTDLP_COOKIES_FILE`**: (Opsiyonel) Eğer YouTube'dan çerezlerle oturum açmak isterseniz `cookies.txt` dosyasının yolu. Bu genellikle bot algılamayı aşmak için kullanılır.

### 3. Yerel Kurulum (Geliştirme Ortamı İçin)

1.  Projeyi klonlayın:
    ```bash
    git clone https://github.com/YOUR_USERNAME/telegram_music_bot.git
    cd telegram_music_bot
    ```
2.  `.env.example` dosyasını `telegram_music_bot/.env` olarak kopyalayın ve ortam değişkenlerini doldurun.
3.  Python bağımlılıklarını kurun (Poetry kullanılarak):
    ```bash
    pip install poetry
    poetry install
    ```
4.  Veritabanı migrasyonlarını çalıştırın (ilk kurulumda):
    ```bash
    alembic revision --autogenerate -m "Initial migration"
    alembic upgrade head
    ```
5.  Botu çalıştırın:
    ```bash
    poetry run python src/main.py
    ```

### 4. GitHub Üzerinden Dağıtım (Railway veya Render ile)

Bu proje, `Dockerfile` sayesinde Railway veya Render gibi platformlara kolayca dağıtılabilir. Bu platformlar, GitHub deponuzu doğrudan bağlayarak otomatik dağıtım (CI/CD) yapabilirler.

1.  **GitHub Repository Oluşturun:** Bu projeyi kendi GitHub hesabınızda yeni bir repository'ye yükleyin.
2.  **Ortam Değişkenlerini GitHub Secrets Olarak Tanımlayın:** Yukarıda belirtilen tüm ortam değişkenlerini GitHub repository'nizin `Settings -> Secrets and variables -> Actions` bölümüne ekleyin.
3.  **Railway/Render Entegrasyonu:**
    *   Railway veya Render hesabınıza giriş yapın.
    *   Yeni bir proje oluşturun ve GitHub deponuzu bağlayın.
    *   Platform, `Dockerfile` dosyasını otomatik olarak algılayacak ve bağımlılıkları kurup botunuzu dağıtacaktır.
    *   Ortam değişkenlerini (GitHub Secrets olarak tanımladıklarınızı) Railway/Render projenizin ortam değişkenleri bölümüne ekleyin. Bu genellikle platformun kendi arayüzünden yapılır ve GitHub Secrets ile senkronize edilebilir.

### 5. Groq API Nasıl Alınır?

1.  [Groq Platformu](https://groq.com/) adresine gidin.
2.  Bir hesap oluşturun veya giriş yapın.
3.  API Anahtarları bölümünden yeni bir API anahtarı oluşturun.

### 6. PostgreSQL Nasıl Kurulur?

Railway veya Render gibi platformlar genellikle yönetilen PostgreSQL hizmetleri sunar. Bu hizmetleri kullanarak kolayca bir veritabanı oluşturabilirsiniz. Yerel geliştirme veya özel sunucu kurulumu için:

1.  Docker kullanarak PostgreSQL başlatın:
    ```bash
    docker run --name some-postgres -e POSTGRES_PASSWORD=mysecretpassword -p 5432:5432 -d postgres
    ```
2.  Veritabanı URL'nizi buna göre ayarlayın: `postgresql+asyncpg://postgres:mysecretpassword@localhost:5432/postgres`

### 7. Neon.tech (Neon Console) Entegrasyonu

Neon.tech, sunucusuz PostgreSQL veritabanı hizmeti sunar ve botunuz için harika bir seçimdir. Ücretsiz katmanı oldukça cömerttir ve kurulumu basittir.

1.  **Neon Hesabı Oluşturun:** [Neon.tech](https://neon.tech/) adresine gidin ve bir hesap oluşturun.
2.  **Yeni Proje Oluşturun:** Neon kontrol panelinde yeni bir proje oluşturun. Otomatik olarak bir veritabanı (genellikle `neondb`) ve bir ana dal (`main`) oluşturulacaktır.
3.  **Bağlantı Dizesini Alın:** Projenizin kontrol panelinde, `Connection Details` bölümünde `Connection String`'i bulacaksınız. Bu dize, botunuzun veritabanına bağlanmak için kullanacağı URL'dir. `psql` veya `Python` sekmesini seçerek uygun formatı alabilirsiniz.
    *   Örnek bir bağlantı dizesi şöyle görünecektir:
        `postgresql://[user]:[password]@[host]/[dbname]?sslmode=require`
4.  **`DATABASE_URL` Ortam Değişkenini Ayarlayın:** Bu bağlantı dizesini, botunuzun `.env` dosyasına (yerel geliştirme için) veya GitHub Secrets / Railway/Render ortam değişkenlerine `DATABASE_URL` olarak ekleyin.
    *   **Önemli:** Neon.tech, tüm bağlantılar için SSL gerektirir. Bağlantı dizenizin sonunda `?sslmode=require` parametresinin olduğundan emin olun. Eğer yoksa, manuel olarak eklemelisiniz.
    *   `sslmode=verify-full` daha güvenli bir seçenektir ancak sertifika doğrulaması gerektirebilir. Basit uygulamalar için `sslmode=require` genellikle yeterlidir.
5.  **Bağlantı Havuzu (Connection Pooling):** Neon, PgBouncer kullanarak bağlantı havuzu sağlar. Bu, botunuzun aynı anda binlerce bağlantıyı yönetmesine olanak tanır. Uygulamanızda ayrıca bir istemci tarafı bağlantı havuzu (örneğin, SQLAlchemy'nin kendi havuzu) kullanıyorsanız, bu durum çift havuzlamaya yol açabilir. Genellikle Neon'un kendi havuzu yeterlidir ve SQLAlchemy'de `poolclass=NullPool` kullanarak istemci tarafı havuzlamayı devre dışı bırakmak iyi bir uygulama olabilir, ancak `asyncpg` varsayılan olarak bunu iyi yönetir.



Railway veya Render gibi platformlar genellikle yönetilen PostgreSQL hizmetleri sunar. Bu hizmetleri kullanarak kolayca bir veritabanı oluşturabilirsiniz. Yerel geliştirme veya özel sunucu kurulumu için:

1.  Docker kullanarak PostgreSQL başlatın:
    ```bash
    docker run --name some-postgres -e POSTGRES_PASSWORD=mysecretpassword -p 5432:5432 -d postgres
    ```
2.  Veritabanı URL'nizi buna göre ayarlayın: `postgresql+asyncpg://postgres:mysecretpassword@localhost:5432/postgres`

### Neon.tech ile Bağlantı Notları:
*   Neon.tech, tüm bağlantılar için SSL gerektirir. `DATABASE_URL` bağlantı dizenizin sonuna `?sslmode=require` veya `?sslmode=verify-full` eklediğinizden emin olun. Örneğin:
    `postgresql+asyncpg://user:password@ep-random-branch-12345.aws.neon.tech/dbname?sslmode=require`
*   Neon, PgBouncer kullanarak bağlantı havuzu sağlar. Uygulamanızda ayrıca bir istemci tarafı bağlantı havuzu (örneğin, SQLAlchemy'nin kendi havuzu) kullanıyorsanız, bu durum çift havuzlamaya yol açabilir. Genellikle Neon'un kendi havuzu yeterlidir.

## Katkıda Bulunma

Katkılarınızı bekliyoruz! Lütfen bir pull request göndermeden önce mevcut kod stiline uyun ve testleri çalıştırın.

## Lisans

Bu proje MIT Lisansı altında lisanslanmıştır. Daha fazla bilgi için `LICENSE` dosyasına bakın.
