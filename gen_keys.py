import os
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
from cryptography.fernet import Fernet

pk = rsa.generate_private_key(public_exponent=65537, key_size=2048, backend=default_backend())
priv = pk.private_bytes(
    encoding=serialization.Encoding.PEM, 
    format=serialization.PrivateFormat.PKCS8, 
    encryption_algorithm=serialization.NoEncryption()
).decode()
pub = pk.public_key().public_bytes(
    encoding=serialization.Encoding.PEM, 
    format=serialization.PublicFormat.SubjectPublicKeyInfo
).decode()
fern = Fernet.generate_key().decode()

print('---F---')
print(fern)
print('---R---')
print(repr(priv))
print('---U---')
print(repr(pub))
