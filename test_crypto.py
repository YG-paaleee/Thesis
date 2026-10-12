#!/usr/bin/env python3
"""
Brgy. San Miguel Emergency LoRa Mesh - AES-128 CBC Test & Verification Script
Matches Thesis Section 3.7 & Section 4.3 (Transmission Security)
"""

import os
import json
import hashlib
import hmac
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.backends import default_backend

# 128-bit Pre-Shared Key (PSK) - 16 bytes matching ESP32 firmware
PRE_SHARED_KEY = bytes([
    0x2B, 0x7E, 0x15, 0x16, 0x28, 0xAE, 0xD2, 0xA6,
    0xAB, 0xF7, 0x15, 0x88, 0x09, 0xCF, 0x4F, 0x3C
])

COMMUNITY_CREDENTIAL = "SANMIGUEL2026"
MAC_KEY_LABEL = b"SanMiguel LoRa CBC MAC v1"
HMAC_SIZE = 32
MAX_PACKET_SIZE = 250

def derive_mac_key() -> bytes:
    """Derive a distinct HMAC key from the AES PSK using a fixed label."""
    return hmac.new(PRE_SHARED_KEY, MAC_KEY_LABEL, hashlib.sha256).digest()

def encrypt_payload(plain_text: str) -> bytes:
    """
    Encrypts with AES-128-CBC + PKCS#7 and appends HMAC-SHA-256.
    Returns: 16-byte IV + Ciphertext + 32-byte HMAC tag
    """
    iv = os.urandom(16)
    padder = padding.PKCS7(128).padder()
    padded_data = padder.update(plain_text.encode('utf-8')) + padder.finalize()

    cipher = Cipher(algorithms.AES(PRE_SHARED_KEY), modes.CBC(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    ciphertext = encryptor.update(padded_data) + encryptor.finalize()

    authenticated_data = iv + ciphertext
    tag = hmac.new(derive_mac_key(), authenticated_data, hashlib.sha256).digest()
    packet = authenticated_data + tag
    if len(packet) > MAX_PACKET_SIZE:
        raise ValueError("Authenticated payload exceeds 250-byte LoRa MTU")
    return packet

def decrypt_payload(encrypted_blob: bytes) -> str:
    """
    Verifies the HMAC before decrypting and unpadding the ciphertext.
    """
    if len(encrypted_blob) < 16 + 16 + HMAC_SIZE or len(encrypted_blob) > MAX_PACKET_SIZE:
        raise ValueError("Invalid authenticated payload length")

    authenticated_data = encrypted_blob[:-HMAC_SIZE]
    received_tag = encrypted_blob[-HMAC_SIZE:]
    expected_tag = hmac.new(derive_mac_key(), authenticated_data, hashlib.sha256).digest()
    if not hmac.compare_digest(received_tag, expected_tag):
        raise ValueError("Message authentication failed; payload was altered or key is incorrect")

    iv = authenticated_data[:16]
    ciphertext = authenticated_data[16:]
    if not ciphertext or len(ciphertext) % 16:
        raise ValueError("Invalid ciphertext length")

    cipher = Cipher(algorithms.AES(PRE_SHARED_KEY), modes.CBC(iv), backend=default_backend())
    decryptor = cipher.decryptor()
    padded_data = decryptor.update(ciphertext) + decryptor.finalize()

    unpadder = padding.PKCS7(128).unpadder()
    plain_bytes = unpadder.update(padded_data) + unpadder.finalize()
    return plain_bytes.decode('utf-8')

def test_pipeline():
    print("=" * 65)
    print("  BRGY. SAN MIGUEL LORA MESH - INTERFACE & SECURITY TEST")
    print("=" * 65)

    # 1. Community Credential Test
    test_cred = "SANMIGUEL2026"
    print(f"\n[1] Testing Community Credential Check...")
    print(f"    Provided Credential: '{test_cred}'")
    if test_cred == COMMUNITY_CREDENTIAL:
        print("    -> PASS: Community access credential verified (Access Granted to Min-Heap).")
    else:
        print("    -> REJECT: Access denied (Anti-Spoofing trigger).")

    # 2. Sample Emergency Message
    sample_emergency = {
        "id": 1042,
        "priority": 1, # k=1 Medical SOS
        "origin": "V6 (Distant Edge)",
        "location": "Purok 4, Coastline",
        "message": "Elderly resident with acute respiratory distress. Water level rising fast."
    }
    raw_json = json.dumps(sample_emergency)
    raw_bytes = len(raw_json.encode('utf-8'))
    print(f"\n[2] Original Plaintext Payload ({raw_bytes} bytes):")
    print(f"    {raw_json}")

    # 3. Encryption Phase
    encrypted = encrypt_payload(raw_json)
    print(f"\n[3] Encrypted Output (IV [16B] + Ciphertext + HMAC [32B]) -> Total {len(encrypted)} bytes:")
    print(f"    Hex: {encrypted.hex()}")

    # Verify LoRa MTU constraint
    print(f"\n[4] LoRa MTU Check (Max 250 bytes limit per Section 4.4.3):")
    if len(encrypted) <= 250:
        print(f"    -> PASS: Payload size ({len(encrypted)} bytes) <= 250 bytes MTU.")
    else:
        print(f"    -> FAIL: Payload exceeds 250 bytes!")

    # 4. Decryption Phase at Main Hub (V1)
    decrypted_str = decrypt_payload(encrypted)
    print(f"\n[5] Decrypted Payload at Main Hub (V1):")
    print(f"    {decrypted_str}")
    
    assert decrypted_str == raw_json, "Integrity check failed: Decrypted does not match original!"
    print("\n[+] SUCCESS: AES-128-CBC + HMAC-SHA-256 Encryption / Integrity / Decryption Pipeline Verified!")
    print("=" * 65)

if __name__ == "__main__":
    test_pipeline()
