# Çukurova Üniversitesi Ders Takip Botu
Created by [@kefeyro](https://t.me/kefeyro)

Bu bot, Çukurova Üniversitesi ders kayıt sistemindeki derslerin kontenjan durumlarını takip eder ve kontenjan açıldığında Telegram üzerinden bildirim gönderir.

## Özellikler

- 🔄 Her 3 dakikada bir kontenjan kontrolü
- 📱 Telegram üzerinden kolay kullanım
- 🔔 Kontenjan açıldığında anında bildirim
- 🔒 Güvenli giriş sistemi

## Kurulum Adımları

### 1. Python Kurulumu

1. [Python'un resmi sitesinden](https://www.python.org/downloads/) Python 3.11 sürümünü indirin
2. Kurulum sırasında "Add Python to PATH" seçeneğini işaretleyin

### 2. Telegram Bot Oluşturma

1. Telegram'da [@BotFather](https://t.me/BotFather) ile konuşma başlatın
2. `/newbot` komutunu gönderin
3. Botunuz için bir isim belirleyin (örn: "CU Ders Takip")
4. Botunuz için bir kullanıcı adı belirleyin (sonu 'bot' ile bitmeli, örn: "cu_ders_takip_bot")
5. BotFather size bir token verecek, bu tokeni kaydedin (örn: `1234567890:ABCdefGHIjklMNOpqrsTUVwxyz`)

### 3. Projeyi İndirme ve Kurulum

1. Bu projeyi bilgisayarınıza indirin:
   ```bash
   git clone https://github.com/erayucar/cu-ders-takip-bot.git
   cd cu-ders-takip-bot
   ```

2. Gerekli Python paketlerini yükleyin:
   ```bash
   pip install -r requirements.txt
   ```
### 5. Yapılandırma

1. Proje klasöründe `.env` dosyası oluşturun:
   ```bash
   touch .env
   ```

2. `.env` dosyasını düzenleyin ve Telegram bot tokeninizi ekleyin:
   ```
   TELEGRAM_BOT_TOKEN=botfather_dan_aldiginiz_token
   ```

## Kullanım

1. Botu başlatın:
   ```bash
   python course_bot.py
   ```

2. Telegram'da botunuza gidin ve `/start` komutunu gönderin

3. `/login` komutu ile sisteme giriş yapın:
   - Kullanıcı adınızı girin
   - Şifrenizi girin

4. `/subscribe` komutu ile ders takibini başlatın

5. Bot artık her 3 dakikada bir kontrol yapacak ve kontenjan açıldığında size bildirim gönderecek

## Komutlar

- `/start` - Botu başlatır ve kullanılabilir komutları gösterir
- `/login` - Sisteme giriş yapmanızı sağlar
- `/subscribe` - Ders takibini başlatır
- `/unsubscribe` - Ders takibini durdurur
- `/stop` - Botu durdurur

## Güvenlik

- Kullanıcı adı ve şifreler sadece oturum sırasında kullanılır, kaydedilmez
- Şifre mesajları otomatik olarak silinir
- Tüm iletişim HTTPS üzerinden şifreli olarak yapılır

## Sorun Giderme

1. "ChromeDriver hatası" alıyorsanız:
   ```bash
   pip install --upgrade selenium webdriver-manager
   ```

3. "Telegram bot hatası" alıyorsanız:
   - Bot tokeninizin doğru olduğundan emin olun
   - `.env` dosyasının doğru formatta olduğunu kontrol edin

## Destek

Sorun yaşarsanız veya yardıma ihtiyacınız olursa:
- Telegram: [@kefeyro](https://t.me/kefeyro)
- GitHub Issues üzerinden bildirebilirsiniz
