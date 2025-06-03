#!/usr/bin/env python
# -*- coding: utf-8 -*-

from datetime import datetime
import os
import json
import logging
import random  # Örnek değerler için kullanıyoruz
import uuid  # Benzersiz ID'ler için
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, CallbackQueryHandler, ConversationHandler
from dotenv import load_dotenv
import dc_motor  # servo yerine dc_motor modülünü import et
import ldr  # LDR modülünü import et
import dhteleven  # DHT11 modülünü import et

# .env dosyasından değişkenleri yükle
load_dotenv()

# Loglama ayarları
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

# Doğru şifre (.env dosyasından al, yoksa varsayılan değer kullan)
CORRECT_PASSWORD = os.getenv("PASSWORD", "12345")

# Dosya isimleri
VERIFIED_USERS_FILE = "verified_users.json"
CONDITIONS_FILE = "conditions.json"

# Aktif dashboard mesajlarını takip etmek için
ACTIVE_DASHBOARDS = {}  # chat_id: message_id şeklinde

# Kullanıcı durumları için sabitler
SELECTING_SENSOR, SELECTING_OPERATOR, ENTERING_VALUE, SELECTING_LOGICAL = range(4)

# Kullanıcı durumları
USER_STATES = {}  # chat_id: {state, temp_condition, condition_type}

# Sensör türleri
SENSOR_TYPES = {
    "temperature": "Sıcaklık",
    "humidity": "Nem",
    "light": "Işık"
}

# Operatörler
OPERATORS = {
    ">": "Büyükse",
    "<": "Küçükse",
    "=": "Eşitse",
    ">=": "Büyük veya Eşitse",
    "<=": "Küçük veya Eşitse"
}

# Mantıksal bağlaçlar
LOGICAL_OPERATORS = {
    "AND": "VE",
    "OR": "VEYA",
    "NONE": "Başka koşul ekleme"
}

# Birimler
UNITS = {
    "temperature": "°C",
    "humidity": "%",
    "light": "lux"
}

# Doğrulanmış kullanıcılar listesini yükle
def load_verified_users():
    if os.path.exists(VERIFIED_USERS_FILE):
        try:
            with open(VERIFIED_USERS_FILE, 'r') as file:
                return json.load(file)
        except json.JSONDecodeError:
            logger.error("Doğrulanmış kullanıcılar dosyası bozuk. Yeni bir liste oluşturuluyor.")
    return []

# Doğrulanmış kullanıcılar listesini kaydet
def save_verified_users(users):
    with open(VERIFIED_USERS_FILE, 'w') as file:
        json.dump(users, file)

# Kullanıcı doğrulanmış mı kontrol et
def is_user_verified(user_id):
    verified_users = load_verified_users()
    return user_id in verified_users

# Kullanıcıyı doğrulanmış olarak kaydet
def verify_user(user_id, username):
    verified_users = load_verified_users()
    if user_id not in verified_users:
        verified_users.append(user_id)
        save_verified_users(verified_users)
        logger.info(f"Yeni kullanıcı doğrulandı: {username} (ID: {user_id})")

# Koşulları yükle
def load_conditions():
    if os.path.exists(CONDITIONS_FILE):
        try:
            with open(CONDITIONS_FILE, 'r') as file:
                conditions = json.load(file)
                return conditions.get("on_conditions", []), conditions.get("off_conditions", [])
        except json.JSONDecodeError:
            logger.error("Koşullar dosyası bozuk. Yeni bir liste oluşturuluyor.")
    return [], []

# Koşulları kaydet
def save_conditions(on_conditions, off_conditions):
    with open(CONDITIONS_FILE, 'w') as file:
        json.dump({
            "on_conditions": on_conditions,
            "off_conditions": off_conditions
        }, file, indent=4)

# Koşulları değerlendir ve motor durumunu belirle
def evaluate_conditions(sensor_data):
    """Koşulları değerlendir ve motor durumunu belirle."""
    try:
        # Koşulları yükle
        on_conditions, off_conditions = load_conditions()
        
        # Aktif durdurma koşullarını kontrol et
        active_off_conditions = [c for c in off_conditions if c["active"]]
        if active_off_conditions:
            # Tüm durdurma koşullarını değerlendir
            stop_conditions_met = all(evaluate_condition(c, sensor_data) for c in active_off_conditions)
            if stop_conditions_met:
                # Tüm koşullar sağlandıysa motoru durdur
                dc_motor.durdur()
                return False
        
        # Aktif çalıştırma koşullarını kontrol et
        active_on_conditions = [c for c in on_conditions if c["active"]]
        if not active_on_conditions:
            # Hiç çalıştırma koşulu yoksa ve motor çalışmıyorsa başlat
            if not dc_motor.durum_kontrol():
                dc_motor.basla()
            return True
        
        # Çalıştırma koşullarını değerlendir
        start_conditions_met = all(evaluate_condition(c, sensor_data) for c in active_on_conditions)
        if start_conditions_met:
            # Tüm koşullar sağlandıysa motoru başlat
            dc_motor.basla()
            return True
        else:
            # Koşullar sağlanmadıysa motoru durdur
            dc_motor.durdur()
            return False
            
    except Exception as e:
        logger.error(f"Koşul değerlendirme hatası: {e}")
        return False

def start(update: Update, context: CallbackContext) -> None:
    """Bot başlatıldığında kullanıcıya karşılama mesajı gönder."""
    user = update.effective_user
    user_id = user.id
    username = user.username or user.first_name
    
    if is_user_verified(user_id):
        update.message.reply_text(
            f'Tekrardan Hoşgeldin @{username}!\nDashboardı açmak için /dashboard yazınız.'
        )        
    else:
        update.message.reply_text(
            f'Merhaba {username}! Lütfen devam etmek için şifreyi girin.'
        )

def dashboard_message(temperature: float, humidity: float, light: float, power: bool, on_conditions: list, off_conditions: list) -> str:
    """Dashboard mesajını oluştur."""
    message = f"📅 Tarih/Saat: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    message += f"🌡️ Sıcaklık: {temperature}°C\n"
    message += f"💧 Nem: {humidity}%\n"
    message += f"💡 Işık: {light} lux\n\n"
    message += f"🔌 Güç: {'✅ Açık' if power else '❌ Kapalı'} \n\n"

    # Sensör verileri
    sensor_data = {
        "temperature": temperature,
        "humidity": humidity,
        "light": light
    }

    # Çalıştırma koşulları
    if on_conditions:
        message += f"🔄 Çalıştırma Koşulları: \n"
        for condition in on_conditions:
            # Koşulun aktif olup olmadığını kontrol et
            if not condition.get("state", True):
                active_emoji = "⚪"  # Koşul pasif ise gri daire göster
            else:
                # Koşulun sağlanıp sağlanmadığını kontrol et
                sensor_type = condition["type"]
                sensor_value = sensor_data[sensor_type]
                condition_value = condition["value"]
                operator = condition["operator"]
                
                is_satisfied = False
                if operator == ">":
                    is_satisfied = sensor_value > condition_value
                elif operator == "<":
                    is_satisfied = sensor_value < condition_value
                elif operator == "=":
                    is_satisfied = sensor_value == condition_value
                elif operator == ">=":
                    is_satisfied = sensor_value >= condition_value
                elif operator == "<=":
                    is_satisfied = sensor_value <= condition_value
                
                active_emoji = "✅" if is_satisfied else "❌"
            
            message += f"{active_emoji} {format_condition(condition)}\n"
    else:
        message += "🔄 Çalıştırma Koşulu Bulunmuyor\n"
    
    message += "\n"
    
    # Kapatma koşulları
    if off_conditions:
        message += f"⏹️ Durdurma Koşulları: \n"
        for condition in off_conditions:
            # Koşulun aktif olup olmadığını kontrol et
            if not condition.get("state", True):
                active_emoji = "⚪"  # Koşul pasif ise gri daire göster
            else:
                # Koşulun sağlanıp sağlanmadığını kontrol et
                sensor_type = condition["type"]
                sensor_value = sensor_data[sensor_type]
                condition_value = condition["value"]
                operator = condition["operator"]
                
                is_satisfied = False
                if operator == ">":
                    is_satisfied = sensor_value > condition_value
                elif operator == "<":
                    is_satisfied = sensor_value < condition_value
                elif operator == "=":
                    is_satisfied = sensor_value == condition_value
                elif operator == ">=":
                    is_satisfied = sensor_value >= condition_value
                elif operator == "<=":
                    is_satisfied = sensor_value <= condition_value
                
                active_emoji = "✅" if is_satisfied else "❌"
            
            message += f"{active_emoji} {format_condition(condition)}\n"
    else:
        message += "⏹️ Durdurma Koşulu Bulunmuyor\n"
    
    return message

def get_dashboard_keyboard():
    """Dashboard için butonları oluştur."""
    keyboard = [
        [
            InlineKeyboardButton("Çalıştırma Koşulu Ekle", callback_data="add_on_condition"),
            InlineKeyboardButton("Durdurma Koşulu Ekle", callback_data="add_off_condition")            
        ],
        [
            InlineKeyboardButton("Koşulları Düzenle", callback_data="manage_conditions")
        ],
        [
            InlineKeyboardButton("Güç Durumunu Değiştir ⚡", callback_data="toggle_power")
        ],
        [
            InlineKeyboardButton("Yenile 🔄", callback_data="refresh")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_condition_management_keyboard():
    """Koşul yönetimi için butonları oluştur."""
    on_conditions, off_conditions = load_conditions()
    keyboard = []
    
    # Çalıştırma koşulları
    if on_conditions:
        keyboard.append([InlineKeyboardButton("--- Çalıştırma Koşulları ---", callback_data="do_nothing")])
        for condition in on_conditions:
            condition_id = condition["id"]
            # Koşulun aktif olup olmadığını gösteren emoji ve durum butonu
            state_emoji = "✅" if condition.get("state", True) else "❌"
            state_text = "Pasif Yap" if condition.get("state", True) else "Aktif Yap"
            
            # Her koşul için iki buton: Durum değiştir ve Sil
            keyboard.append([
                InlineKeyboardButton(
                    f"{state_emoji} {format_condition(condition)}",
                    callback_data=f"toggle_on_condition:{condition_id}"
                ),
                InlineKeyboardButton(
                    f"Sil 🗑️", 
                    callback_data=f"delete_on_condition:{condition_id}"
                )
            ])
    
    # Kapatma koşulları
    if off_conditions:
        keyboard.append([InlineKeyboardButton("--- Durdurma Koşulları ---", callback_data="do_nothing")])
        for condition in off_conditions:
            condition_id = condition["id"]
            # Koşulun aktif olup olmadığını gösteren emoji ve durum butonu
            state_emoji = "✅" if condition.get("state", True) else "❌"
            state_text = "Pasif Yap" if condition.get("state", True) else "Aktif Yap"
            
            # Her koşul için iki buton: Durum değiştir ve Sil
            keyboard.append([
                InlineKeyboardButton(
                    f"{state_emoji} {format_condition(condition)}",
                    callback_data=f"toggle_off_condition:{condition_id}"
                ),
                InlineKeyboardButton(
                    f"Sil 🗑️", 
                    callback_data=f"delete_off_condition:{condition_id}"
                )
            ])
    
    # Geri butonu
    keyboard.append([InlineKeyboardButton("◀️ Geri", callback_data="back_to_dashboard")])
    
    return InlineKeyboardMarkup(keyboard)

def get_sensor_data():
    """Sensör verilerini al."""
    try:
        # LDR'den ışık değerini al
        try:
            light = ldr.get_lux()
        except Exception as e:
            logger.error(f"LDR okuma hatası: {e}")
            light = 0.0
        
        # DHT11'den sıcaklık ve nem değerlerini al
        try:
            result = dhteleven.get_temperature_and_humidity()
            if result is None:
                temperature, humidity = 0.0, 0.0
            else:
                temperature, humidity = result
                # -1 değerlerini 0'a çevir
                if temperature < 0:
                    temperature = 0.0
                if humidity < 0:
                    humidity = 0.0
        except Exception as e:
            logger.error(f"DHT11 okuma hatası: {e}")
            temperature, humidity = 0.0, 0.0
        
        sensor_data = {
            "temperature": temperature,
            "humidity": humidity,
            "light": light
        }
        
        # Motor durumunu kontrol et
        sensor_data["power"] = dc_motor.durum_kontrol()
        
        # Koşul listelerini ekle
        on_conditions, off_conditions = load_conditions()
        sensor_data["on_conditions"] = on_conditions
        sensor_data["off_conditions"] = off_conditions
        
        return sensor_data
    except Exception as e:
        logger.error(f"Sensör verisi alma hatası: {e}")
        # Hata durumunda varsayılan değerler
        return {
            "temperature": 0.0,
            "humidity": 0.0,
            "light": 0.0,
            "power": False,
            "on_conditions": [],
            "off_conditions": []
        }

def format_condition(condition):
    """Koşulu okunabilir bir formatta döndür."""
    sensor_type = condition["type"]
    operator = condition["operator"]
    value = condition["value"]
    logical = condition.get("logical", "NONE")
    
    # Türkçe isimlerini al
    sensor_name = SENSOR_TYPES[sensor_type]
    unit = UNITS[sensor_type]
    
    # Formatlanmış metin
    text = f"{sensor_name} {operator} {value}{unit}"
    
    # Mantıksal bağlaç varsa ekle
    if logical != "NONE":
        text += f" {LOGICAL_OPERATORS[logical]}"
    
    return text

# Koşul ekleme fonksiyonları
def start_add_condition(update: Update, context: CallbackContext, condition_type="on"):
    """Koşul ekleme sürecini başlat."""
    chat_id = update.effective_chat.id
    
    # Kullanıcı durumunu ayarla
    USER_STATES[chat_id] = {
        "state": SELECTING_SENSOR,
        "temp_condition": {
            "id": str(uuid.uuid4()),  # Benzersiz ID
            "state": True  # Başlangıçta aktif
        },
        "condition_type": condition_type  # "on" veya "off"
    }
    
    # Sensör seçimi için klavye oluştur
    keyboard = []
    for sensor_id, sensor_name in SENSOR_TYPES.items():
        keyboard.append([sensor_name])
    
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
    
    # Callback'den gelen komutlar için farklı işlem yap
    if update.callback_query:
        # Önce callback'i işle
        update.callback_query.answer()
        
        # Mesajı gönder
        context.bot.send_message(
            chat_id=chat_id,
            text="Hangi sensör için koşul eklemek istiyorsunuz?",
            reply_markup=reply_markup
        )
    else:
        # Normal mesaj için
        update.effective_message.reply_text(
            "Hangi sensör için koşul eklemek istiyorsunuz?",
            reply_markup=reply_markup
        )
    
    # Conversation durumunu güncelle
    return SELECTING_SENSOR

def handle_sensor_selection(update: Update, context: CallbackContext):
    """Kullanıcının seçtiği sensör türünü işle."""
    chat_id = update.effective_chat.id
    text = update.message.text
    
    # Sensör ID'sini bul
    sensor_id = None
    for sid, name in SENSOR_TYPES.items():
        if name == text:
            sensor_id = sid
            break
    
    if not sensor_id:
        update.message.reply_text("Geçersiz sensör türü. Lütfen tekrar deneyin.")
        return SELECTING_SENSOR
    
    # Seçilen sensörü geçici koşula kaydet
    USER_STATES[chat_id]["temp_condition"]["type"] = sensor_id
    
    # Operatör seçimi için klavye oluştur
    keyboard = []
    for op_id, op_name in OPERATORS.items():
        keyboard.append([f"{op_id} ({op_name})"])
    
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
    
    # Operatör sorma mesajını gönder
    update.message.reply_text(
        f"Hangi operatörü kullanmak istiyorsunuz?",
        reply_markup=reply_markup
    )
    
    return SELECTING_OPERATOR

def handle_operator_selection(update: Update, context: CallbackContext):
    """Kullanıcının seçtiği operatörü işle."""
    chat_id = update.effective_chat.id
    text = update.message.text.split()[0]  # İlk kelimeyi al (operatörü)
    
    if text not in OPERATORS:
        update.message.reply_text("Geçersiz operatör. Lütfen tekrar deneyin.")
        return SELECTING_OPERATOR
    
    # Seçilen operatörü geçici koşula kaydet
    USER_STATES[chat_id]["temp_condition"]["operator"] = text
    
    # Sensör türünü al
    sensor_type = USER_STATES[chat_id]["temp_condition"]["type"]
    unit = UNITS[sensor_type]
    
    # Değer girmesi için kullanıcıya sor
    update.message.reply_text(
        f"Karşılaştırma değerini girin ({unit}):",
        reply_markup=ReplyKeyboardRemove()
    )
    
    return ENTERING_VALUE

def handle_value_entry(update: Update, context: CallbackContext):
    """Kullanıcının girdiği değeri işle."""
    chat_id = update.effective_chat.id
    text = update.message.text
    
    try:
        value = float(text)
    except ValueError:
        update.message.reply_text("Lütfen geçerli bir sayı girin.")
        return ENTERING_VALUE
    
    # Girilen değeri geçici koşula kaydet
    USER_STATES[chat_id]["temp_condition"]["value"] = value
    
    # Mantıksal bağlaç seçimi için klavye oluştur
    keyboard = []
    for logical_id, logical_name in LOGICAL_OPERATORS.items():
        keyboard.append([logical_name])
    
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
    
    # Mantıksal bağlaç sorma mesajını gönder
    update.message.reply_text(
        "Bu koşulu başka bir koşulla bağlamak istiyor musunuz?",
        reply_markup=reply_markup
    )
    
    return SELECTING_LOGICAL

def handle_logical_selection(update: Update, context: CallbackContext):
    """Kullanıcının seçtiği mantıksal bağlacı işle."""
    chat_id = update.effective_chat.id
    text = update.message.text
    
    # Mantıksal operatör ID'sini bul
    logical_id = None
    for lid, name in LOGICAL_OPERATORS.items():
        if name == text:
            logical_id = lid
            break
    
    if not logical_id:
        update.message.reply_text("Geçersiz seçim. Lütfen tekrar deneyin.")
        return SELECTING_LOGICAL
    
    # Mantıksal bağlacı geçici koşula kaydet (NONE değilse)
    if logical_id != "NONE":
        USER_STATES[chat_id]["temp_condition"]["logical"] = logical_id
    
    # Geçici koşulu kalıcı koşullara ekle
    condition_type = USER_STATES[chat_id]["condition_type"]
    new_condition = USER_STATES[chat_id]["temp_condition"]
    
    on_conditions, off_conditions = load_conditions()
    
    if condition_type == "on":
        on_conditions.append(new_condition)
    else:  # "off"
        off_conditions.append(new_condition)
    
    # Koşulları kaydet
    save_conditions(on_conditions, off_conditions)
    
    # Klavyeyi kaldır
    update.message.reply_text(
        f"Koşul başarıyla eklendi: {format_condition(new_condition)}",
        reply_markup=ReplyKeyboardRemove()
    )
    
    # Eğer başka koşul eklemek istiyorsa yeni bir koşul ekleme sürecini başlat
    if logical_id != "NONE":
        return start_add_condition(update, context, condition_type)
    else:
        # Koşul ekleme sürecini bitir ve dashboard'a dön
        # Önce durumu temizle
        USER_STATES.pop(chat_id, None)
        
        # Dashboard'ı göster
        context.dispatcher.bot.send_message(
            chat_id=chat_id,
            text="Koşul ekleme işlemi tamamlandı. Dashboard'ı görüntülemek için /dashboard komutunu kullanabilirsiniz."
        )
        return ConversationHandler.END

def cancel_condition(update: Update, context: CallbackContext):
    """Koşul ekleme işlemini iptal et."""
    chat_id = update.effective_chat.id
    
    # Durumu temizle
    USER_STATES.pop(chat_id, None)
    
    # Klavyeyi kaldır
    update.message.reply_text(
        "Koşul ekleme işlemi iptal edildi.",
        reply_markup=ReplyKeyboardRemove()
    )
    
    return ConversationHandler.END

def delete_condition(update: Update, context: CallbackContext, condition_id, condition_type):
    """Belirtilen koşulu sil."""
    on_conditions, off_conditions = load_conditions()
    
    if condition_type == "on":
        on_conditions = [c for c in on_conditions if c["id"] != condition_id]
    else:  # "off"
        off_conditions = [c for c in off_conditions if c["id"] != condition_id]
    
    # Koşulları kaydet
    save_conditions(on_conditions, off_conditions)
    
    return True

def toggle_condition(update: Update, context: CallbackContext, condition_id, condition_type):
    """Belirtilen koşulun durumunu değiştir (aktif/pasif)."""
    on_conditions, off_conditions = load_conditions()
    
    if condition_type == "on":
        for condition in on_conditions:
            if condition["id"] == condition_id:
                condition["state"] = not condition.get("state", True)
                break
    else:  # "off"
        for condition in off_conditions:
            if condition["id"] == condition_id:
                condition["state"] = not condition.get("state", True)
                break
    
    # Koşulları kaydet
    save_conditions(on_conditions, off_conditions)
    
    return True

def handle_message(update: Update, context: CallbackContext) -> None:
    """Gelen mesajları işle ve şifre kontrolü yap."""
    user = update.effective_user
    user_id = user.id
    username = user.username or user.first_name
    text = update.message.text
    chat_id = update.effective_chat.id
    
    # Eğer kullanıcı koşul ekleme sürecindeyse, bu mesajı işleme
    if chat_id in USER_STATES:
        # ConversationHandler bu mesajı işleyecek, burada bir şey yapma
        return
    
    # Kullanıcı zaten doğrulanmışsa, mesajı normal işle
    if is_user_verified(user_id):
        update.message.reply_text(f"Mesajınız alındı: {text}")
        return
    
    # Kullanıcı doğrulanmamışsa, şifre kontrolü yap
    if text == CORRECT_PASSWORD:
        verify_user(user_id, username)
        update.message.reply_text(
            f"Şifre doğru! Hoş geldiniz @{username}.\n Kontrol merkezini açmak için /dashboard yazınız."
        )
    else:
        update.message.reply_text(
            "Yanlış şifre. Lütfen tekrar deneyin."
        )

def handle_callback_query(update: Update, context: CallbackContext):
    """Callback query'leri işle."""
    query = update.callback_query
    query.answer()
    
    if query.data == "dashboard":
        # Dashboard'u göster
        sensor_data = get_sensor_data()
        query.message.edit_text(
            text=format_dashboard(sensor_data),
            reply_markup=get_dashboard_keyboard(),
            parse_mode='HTML'
        )
        return
    
    if query.data == "toggle_power":
        # Sensör verilerini al
        sensor_data = get_sensor_data()
        
        try:
            # Güç durumunu tersine çevir ve motoru çalıştır/durdur
            if sensor_data["power"]:
                if dc_motor.durdur():  # Başarılı olduğunda True döner
                    sensor_data["power"] = False
                    query.answer("Motor manuel olarak durduruldu.")
                else:
                    query.answer("Motor durdurulurken bir hata oluştu!")
                    return
            else:
                if dc_motor.basla():  # Başarılı olduğunda True döner
                    sensor_data["power"] = True
                    query.answer("Motor manuel olarak çalıştırıldı.")
                else:
                    query.answer("Motor çalıştırılırken bir hata oluştu!")
                    return
            
            # Mesajı güncelle
            query.message.edit_text(
                text=format_dashboard(sensor_data),
                reply_markup=get_dashboard_keyboard(),
                parse_mode='HTML'
            )
        except Exception as e:
            logger.error(f"Güç durumu değiştirme hatası: {e}")
            query.answer("Bir hata oluştu! Lütfen tekrar deneyin.")
            return

def update_motor_status():
    """Sensör verilerine göre motor durumunu güncelle."""
    try:
        # LDR'den ışık değerini al
        try:
            light = ldr.get_lux()
        except Exception as e:
            logger.error(f"LDR okuma hatası: {e}")
            light = 0.0
        
        # DHT11'den sıcaklık ve nem değerlerini al
        try:
            result = dhteleven.get_temperature_and_humidity()
            if result is None:
                temperature, humidity = 0.0, 0.0
            else:
                temperature, humidity = result
                # -1 değerlerini 0'a çevir
                if temperature < 0:
                    temperature = 0.0
                if humidity < 0:
                    humidity = 0.0
        except Exception as e:
            logger.error(f"DHT11 okuma hatası: {e}")
            temperature, humidity = 0.0, 0.0
        
        sensor_data = {
            "temperature": temperature,
            "humidity": humidity,
            "light": light
        }
        
        # Koşulları değerlendirerek motor durumunu belirle
        power = evaluate_conditions(sensor_data)
        
        # Motor durumunu logla
        logger.info(f"Motor durumu güncellendi: {'AÇIK' if power else 'KAPALI'}")
        logger.info(f"Sensör değerleri: Sıcaklık={sensor_data['temperature']}°C, Nem={sensor_data['humidity']}%, Işık={sensor_data['light']} lux")
        
        return power
    except Exception as e:
        logger.error(f"Motor durumu güncelleme hatası: {e}")
        return False

def auto_refresh_dashboard(context: CallbackContext) -> None:
    """Dashboard'u otomatik olarak yenile."""
    # Job context'inden chat_id'yi al
    chat_id = context.job.context
    
    # Eğer bu chat_id için aktif bir dashboard yoksa işlemi iptal et
    if chat_id not in ACTIVE_DASHBOARDS:
        return
    
    # Mesaj ID'sini al
    message_id = ACTIVE_DASHBOARDS[chat_id]
    
    # Motor durumunu güncelle
    update_motor_status()
    
    # Sensör verilerini al
    sensor_data = get_sensor_data()
    
    try:
        # Mesajı güncelle
        context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=dashboard_message(
                sensor_data["temperature"], 
                sensor_data["humidity"], 
                sensor_data["light"], 
                sensor_data["power"], 
                sensor_data["on_conditions"], 
                sensor_data["off_conditions"]
            ),
            reply_markup=get_dashboard_keyboard()
        )
        logger.info(f"Chat ID {chat_id} için dashboard otomatik olarak yenilendi.")
    except Exception as e:
        # Hata durumunda job'ı kaldır ve hata mesajını logla
        logger.error(f"Dashboard yenileme hatası: {e}")
        ACTIVE_DASHBOARDS.pop(chat_id, None)
        jobs = context.job_queue.get_jobs_by_name(f"refresh_{chat_id}")
        if jobs:
            for job in jobs:
                job.schedule_removal()

def dashboard(update: Update, context: CallbackContext) -> None:
    """Dashboard mesajı ve butonlarını göster."""
    # Sensör verilerini al
    sensor_data = get_sensor_data()
    
    # Mesajı gönder
    message = update.message.reply_text(
        dashboard_message(
            sensor_data["temperature"], 
            sensor_data["humidity"], 
            sensor_data["light"], 
            sensor_data["power"], 
            sensor_data["on_conditions"], 
            sensor_data["off_conditions"]
        ), 
        reply_markup=get_dashboard_keyboard()
    )
    
    # Aktif dashboard'ları takip et
    chat_id = update.effective_chat.id
    ACTIVE_DASHBOARDS[chat_id] = message.message_id
    
    # Otomatik yenileme için job ekle
    # Eğer daha önce job eklenmişse kaldır
    existing_jobs = context.job_queue.get_jobs_by_name(f"refresh_{chat_id}")
    if existing_jobs:
        for job in existing_jobs:
            job.schedule_removal()
    
    # 10 saniyede bir yenileme job'ını ekle
    context.job_queue.run_repeating(
        auto_refresh_dashboard, 
        interval=10, 
        first=10,
        context=chat_id,
        name=f"refresh_{chat_id}"
    )
    
    update.message.reply_text("Dashboard her 10 saniyede bir otomatik olarak yenilenecektir.")

def main() -> None:
    """Bot'u başlat."""
    # .env dosyasından TOKEN'ı al, yoksa kullanıcıya uyarı ver
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        logger.error("TELEGRAM_BOT_TOKEN bulunamadı. .env dosyasını kontrol edin.")
        return

    # Motor durumunu kontrol et
    motor_status = dc_motor.durum_kontrol()
    logger.info(f"Başlangıçta motor durumu: {'AÇIK' if motor_status else 'KAPALI'}")
    
    # Updater oluştur ve token'ı geçir
    updater = Updater(token)

    # Dispatcher al
    dispatcher = updater.dispatcher
    
    # Koşul ekleme conversation handler'ı
    condition_conv_handler = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(
                lambda update, context: start_add_condition(update, context, "on") if update.callback_query.data == "add_on_condition" else start_add_condition(update, context, "off"),
                pattern="^add_on_condition$|^add_off_condition$"
            )
        ],
        states={
            SELECTING_SENSOR: [MessageHandler(Filters.text & ~Filters.command, handle_sensor_selection)],
            SELECTING_OPERATOR: [MessageHandler(Filters.text & ~Filters.command, handle_operator_selection)],
            ENTERING_VALUE: [MessageHandler(Filters.text & ~Filters.command, handle_value_entry)],
            SELECTING_LOGICAL: [MessageHandler(Filters.text & ~Filters.command, handle_logical_selection)]
        },
        fallbacks=[CommandHandler("cancel", cancel_condition)],
        allow_reentry=True,
        name="condition_conversation"
    )

    # Komut işleyicileri ekle
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("dashboard", dashboard))
    
    # Koşul ekleme conversation handler'ını ekle
    dispatcher.add_handler(condition_conv_handler)
    
    # Diğer butonlar için callback handler'ı ekle
    dispatcher.add_handler(CallbackQueryHandler(handle_callback_query))
    
    # Mesaj işleyicisi ekle (en sonda olmalı)
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

    # Bot'u başlat
    updater.start_polling()
    logger.info("Bot başlatıldı. Durdurmak için Ctrl+C tuşlarına basın.")

    # Bot'u sonlandırılana kadar çalışır durumda tut
    updater.idle()
    
    # Program sonlandığında GPIO pinlerini temizle
    dc_motor.cleanup()

if __name__ == '__main__':
    main() 