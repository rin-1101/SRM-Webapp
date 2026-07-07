from cryptography.fernet import Fernet
import json


with open("key.bin", "rb") as file_object:
    for line in file_object:
        key = line

cipher_suite = Fernet(key)

with open("accts.bin", "rb") as file_object:
    for line in file_object:
        encryptedpwd = line
unciphered_text = cipher_suite.decrypt(encryptedpwd)
accounts = json.loads(unciphered_text.decode("utf-8"))
