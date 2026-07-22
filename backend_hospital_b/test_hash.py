import bcrypt

# Database ထဲက Hash (ခင်ဗျားရဲ့ Database ထဲက အတိအကျ)
hashed = "$2b$12$imxEpEdjNIyEk0/W3swL8OY14GmzRaWYApQX/jiJS7JUhnAqcgQ4K"
password = "admin123"

print(f"🔍 Hashed: {hashed}")
print(f"🔍 Hashed length: {len(hashed)}")
print(f"🔍 Password: {password}")

try:
    result = bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    print(f"✅ Result: {result}")
except Exception as e:
    print(f"❌ Error: {e}")