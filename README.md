# IoT Sensör Kontrol Botu

Bu proje, Raspberry Pi üzerinde çalışan ve Telegram üzerinden kontrol edilebilen bir IoT sensör kontrol sistemidir. Sistem, sıcaklık, nem ve ışık sensörlerinden veri toplar ve bu verilere göre DC motoru kontrol eder.

## Özellikler

- 🔍 **Sensör Okuma**
  - DHT11 ile sıcaklık ve nem ölçümü
  - LDR ile ışık şiddeti ölçümü
  - 10 saniyede bir otomatik veri güncelleme

- 🎮 **Telegram Bot Kontrolü**
  - Gerçek zamanlı sensör verilerini görüntüleme
  - DC motoru manuel kontrol
  - Koşullu otomatik kontrol sistemi

- ⚙️ **Koşullu Kontrol Sistemi**
  - Çalıştırma koşulları tanımlama
  - Durdurma koşulları tanımlama
  - AND/OR mantıksal operatörleri ile koşul birleştirme
  - Koşulları aktif/pasif yapma
  - Koşulları silme

- 🔄 **Sistem Sıfırlama**
  - Tüm koşulları sıfırlama
  - DC motoru durdurma
  - Sensör verilerini sıfırlama
  - Onaylı/onaysız sıfırlama seçeneği

## Donanım Gereksinimleri

- Raspberry Pi 3 ve üzeri
- DHT11 (Sıcaklık ve Nem Sensörü)
- LDR (Işık Sensörü)
- DC Motor
- L293D Motor Sürücü
- 5V 1A Adaptör
- Klemens Çıkışlı DC Female Barrel Jack
- Gerekli bağlantı kabloları ve dirençler

## Bağlantılar

### DHT11 Sensörü
- VCC -> 3.3V
- DATA -> GPIO14
- GND -> GND

### LDR Sensörü
- VCC -> 3.3V
- DATA -> GPIO17
- GND -> GND

### DC Motor (L298N üzerinden)
- IN1 -> GPIO18
- IN2 -> GPIO23
- ENA -> GPIO24
- VCC -> 12V
- GND -> GND

## Kurulum

1. Projeyi klonlayın:
```bash
git clone https://github.com/0xAtasoy/inf208-e24-proje-odevi.git
cd inf208-e24-proje-odevi
```

2. Sanal ortam oluşturun ve aktifleştirin:
```bash
python3 -m venv venv
source venv/bin/activate
```

3. Gerekli Python paketlerini yükleyin:
```bash
pip install -r requirements.txt
```

5. `.env` dosyası oluşturun . `TELEGRAM_BOT_TOKEN` ve `PASSWORD` bilgilerini girin.


## Kullanım

1. Botu başlatın:
```bash
python bot.py
```

2. Telegram'da botu bulun ve `/start` komutunu gönderin.

3. Dashboard'u görüntülemek için `/dashboard` komutunu kullanın.

4. Koşul eklemek için:
   - "Koşulları Yönet" butonuna tıklayın
   - "Çalıştırma Koşulu Ekle" veya "Durdurma Koşulu Ekle" seçin
   - Sensör tipini seçin (Sıcaklık, Nem, Işık)
   - Operatörü seçin (>, <, =)
   - Değeri girin
   - Mantıksal operatörü seçin (AND/OR)

5. Sistemi sıfırlamak için:
   - Terminal üzerinden:
     ```bash
     python reset_bot.py
     ```
   - Onay istemeden sıfırlamak için:
     ```bash
     python reset_bot.py --force
     ```

## Komutlar

- `/start` - Botu başlatır
- `/dashboard` - Sensör verilerini ve koşulları görüntüler
- `/cancel` - Koşul ekleme işlemini iptal eder

## Sistem Sıfırlama

Sistem sıfırlama işlemi şunları yapar:
- Tüm çalıştırma ve durdurma koşullarını siler
- DC motoru durdurur
- Sensör verilerini sıfırlar
- Koşul dosyalarını temizler

Sıfırlama işlemi iki şekilde yapılabilir:
1. **Onaylı Sıfırlama**: Kullanıcıdan onay ister
2. **Onaysız Sıfırlama**: `--force` parametresi ile direkt sıfırlar

## Lisans

Bu proje MIT lisansı altında lisanslanmıştır. Detaylar için [LICENSE](LICENSE) dosyasına bakın.

## İletişim

Sorularınız veya önerileriniz için GitHub üzerinden issue açabilirsiniz. 