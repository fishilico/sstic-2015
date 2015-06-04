#!/usr/bin/env python3
"""Brute-force the User-Agent used to encrypt a zip archive"""
from Crypto.Cipher import AES
from hashlib import sha1

from . import generate_useragents

# Read the encrypted data and the SHA-1 hash of the decrypted data
with open('stage4.js', 'r') as f:
    encrypted_hex = f.readline().strip().lstrip('var data = "').rstrip('";')
    encrypted = bytes.fromhex(encrypted_hex)
    hash_hex = f.readline().strip().lstrip('var hash = "').rstrip('";')

for useragent in generate_useragents.gen_ua():
    iv = useragent[useragent.index('(') + 1:][:16].encode('ascii')
    key = useragent[useragent.index(')') - 16:][:16].encode('ascii')
    assert len(iv) == len(key) == 16
    decrypted = AES.new(key, AES.MODE_CBC, iv).decrypt(encrypted)
    if sha1(decrypted).hexdigest() == hash_hex:
        print("SUCCESS!", useragent)
        break
    # Remove padding, if valid
    padlen = decrypted[-1]
    if padlen <= 16 and all(d == padlen for d in decrypted[-padlen:]):
        decrypted = decrypted[:-padlen]
    # Re-test the hash
    if sha1(decrypted).hexdigest() == hash_hex:
        print("SUCCESS!", useragent)
        break
    # Test if the key is correct
    if decrypted[-22:-20] == b'PK':
        print("Potential ZIP, key may be good...", key, useragent)
