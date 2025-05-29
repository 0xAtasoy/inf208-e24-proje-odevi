# IoT Telegram Bot

Bu proje, IoT sensörlerini (sıcaklık, nem, ışık) izleyen ve bir röleyi kontrol eden bir Telegram botu içerir. Bot, sensör verilerini görüntüler ve kullanıcı tanımlı koşullara bağlı olarak röleyi çalıştırır veya durdurur.

## Özellikler

- 📊 **Gerçek Zamanlı Dashboard**: Sensör verilerini ve röle durumunu gösteren otomatik yenilenen dashboard
- 🔐 **Kullanıcı Doğrulama**: Sadece onaylanmış kullanıcılar botu kullanabilir
- ⚙️ **Koşullu Kontrol**: Röleyi belirli sensör koşullarına bağlı olarak otomatik çalıştırma/durdurma
- 📱 **Kullanıcı Dostu Arayüz**: Kolay kullanılabilir Telegram arayüzü

## Kurulum

1. Bu repository'yi klonlayın:
```
git clone https://github.com/KULLANICI_ADI/iot-telegram-bot.git
cd iot-telegram-bot
```

2. Gerekli bağımlılıkları yükleyin:
```
pip install -r requirements.txt
```

3. `.env` dosyası oluşturun ve Telegram bot token'ınızı ekleyin:
```
TELEGRAM_BOT_TOKEN=your_bot_token_here
```

## Kullanım

1. Botu başlatın:
```
python bot.py
```

2. Telegram'da botu açın ve `/start` komutunu gönderin.

3. Onaylanmış bir kullanıcı iseniz, `/dashboard` komutu ile sensör verilerini görüntüleyebilirsiniz.

4. Röle için çalıştırma ve durdurma koşulları eklemek için dashboard menüsünü kullanın.

## Bot Komutları

- `/start` - Botu başlatır ve temel bilgileri gösterir
- `/dashboard` - Sensör dashboard'ını gösterir
- `/reset` - Bot ayarlarını sıfırlar (sadece onaylanmış kullanıcılar için)

## Bot Sıfırlama

Terminalde aşağıdaki komutu çalıştırarak botu sıfırlayabilirsiniz:
```
python reset_bot.py
```

Veya onay istemeden sıfırlamak için:
```
python reset_bot.py --force
```

## Teknik Detaylar

Bot, şu bileşenlerden oluşur:
- Python Telegram Bot API (python-telegram-bot)
- Sensör verilerini simüle eden modüller
- Koşullu mantık işleyicisi
- Veri saklama mekanizması (JSON dosyaları)

## Lisans

Bu proje MIT lisansı altında lisanslanmıştır - detaylar için [LICENSE](LICENSE) dosyasına bakın. 