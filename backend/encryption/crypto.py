from cryptography.fernet import Fernet

def generate_key():
    return Fernet.generate_key()

def encrypt_message(message, key):
    cipher = Fernet(key)
    return cipher.encrypt(message.encode())

def decrypt_message(encrypted_message, key):
    cipher = Fernet(key)
    return cipher.decrypt(encrypted_message).decode()