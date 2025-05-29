#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import json
import sys

# Dosya isimleri
VERIFIED_USERS_FILE = "verified_users.json"
CONDITIONS_FILE = "conditions.json"

def reset_all():
    """Tüm bot verilerini sıfırla."""
    print("Bot sıfırlama işlemi başlatılıyor...")
    
    # Onaylanmış kullanıcıları sıfırla
    try:
        if os.path.exists(VERIFIED_USERS_FILE):
            os.remove(VERIFIED_USERS_FILE)
            print(f"✅ {VERIFIED_USERS_FILE} dosyası silindi.")
        else:
            print(f"ℹ️ {VERIFIED_USERS_FILE} dosyası zaten mevcut değil.")
    except Exception as e:
        print(f"❌ {VERIFIED_USERS_FILE} dosyası silinirken hata: {e}")
    
    # Koşulları sıfırla
    try:
        if os.path.exists(CONDITIONS_FILE):
            # Koşulları tamamen silmek yerine boş liste olarak kaydet
            with open(CONDITIONS_FILE, 'w') as file:
                json.dump({"on_conditions": [], "off_conditions": []}, file, indent=4)
            print(f"✅ {CONDITIONS_FILE} dosyası sıfırlandı.")
        else:
            # Dosya yoksa yeni oluştur
            with open(CONDITIONS_FILE, 'w') as file:
                json.dump({"on_conditions": [], "off_conditions": []}, file, indent=4)
            print(f"✅ {CONDITIONS_FILE} dosyası oluşturuldu.")
    except Exception as e:
        print(f"❌ {CONDITIONS_FILE} dosyası sıfırlanırken hata: {e}")
    
    print("\n🔄 Bot verileri başarıyla sıfırlandı!")
    print("⚠️ Bot'u yeniden başlatmanız gerekebilir!")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--help":
        print("Bu script, bot'un tüm verilerini sıfırlar.")
        print("Kullanım: python reset_bot.py")
        print("  --help    Bu yardım mesajını gösterir")
        print("  --force   Onay istemeden sıfırlama yapar")
        sys.exit(0)
    
    # Eğer --force parametresi yoksa onay iste
    if len(sys.argv) == 1 or sys.argv[1] != "--force":
        confirm = input("⚠️ Bu işlem bot'un tüm verilerini sıfırlayacak. Devam etmek istiyor musunuz? (E/H): ")
        if confirm.lower() not in ["e", "evet", "y", "yes"]:
            print("İşlem iptal edildi.")
            sys.exit(0)
    
    reset_all() 