#ifndef AES_CRYPTO_H
#define AES_CRYPTO_H

#include <Arduino.h>
#include "mbedtls/aes.h"
#include "mbedtls/md.h"
#include "esp_system.h"

// 128-bit Pre-Shared Key (PSK) - 16 bytes for AES-128
// As specified in Thesis Section 4.3 (Transmission Security)
static const uint8_t PRE_SHARED_KEY[16] = {
    0x2B, 0x7E, 0x15, 0x16, 0x28, 0xAE, 0xD2, 0xA6,
    0xAB, 0xF7, 0x15, 0x88, 0x09, 0xCF, 0x4F, 0x3C
};

// HMAC key is derived with a fixed label so it is separate from the AES key.
static const char MAC_KEY_LABEL[] = "SanMiguel LoRa CBC MAC v1";
static const size_t HMAC_SIZE = 32; // SHA-256 tag
static const size_t MAX_ENCRYPTED_PACKET_SIZE = 250; // Thesis LoRa MTU limit

// Community Access Credential (Single Shared Secret for Barangay San Miguel)
#define COMMUNITY_ACCESS_CREDENTIAL "SANMIGUEL2026"

class AESCrypto {
private:
    static bool computeMacKey(uint8_t *macKey) {
        const mbedtls_md_info_t *mdInfo = mbedtls_md_info_from_type(MBEDTLS_MD_SHA256);
        if (!mdInfo) return false;
        return mbedtls_md_hmac(mdInfo, PRE_SHARED_KEY, sizeof(PRE_SHARED_KEY),
                               reinterpret_cast<const unsigned char *>(MAC_KEY_LABEL),
                               sizeof(MAC_KEY_LABEL) - 1, macKey) == 0;
    }

    static bool computeHmac(const uint8_t *data, size_t dataLen, uint8_t *tag) {
        const mbedtls_md_info_t *mdInfo = mbedtls_md_info_from_type(MBEDTLS_MD_SHA256);
        if (!mdInfo) return false;
        uint8_t macKey[HMAC_SIZE];
        if (!computeMacKey(macKey)) return false;
        int ret = mbedtls_md_hmac(mdInfo, macKey, sizeof(macKey), data, dataLen, tag);
        memset(macKey, 0, sizeof(macKey));
        return ret == 0;
    }

    static bool tagsMatch(const uint8_t *a, const uint8_t *b, size_t len) {
        uint8_t difference = 0;
        for (size_t i = 0; i < len; i++) difference |= a[i] ^ b[i];
        return difference == 0;
    }

public:
    // Generate cryptographically random 16-byte IV
    static void generateIV(uint8_t *iv) {
        esp_fill_random(iv, 16);
    }

    // Encrypt with AES-128-CBC/PKCS#7, then authenticate IV + ciphertext with HMAC-SHA-256.
    // Output format: [16-byte IV] + [Ciphertext] + [32-byte HMAC tag]
    static bool encrypt(const char *plainText, size_t plainLen, uint8_t *outBuffer, size_t &outLen, size_t maxOutLen) {
        outLen = 0;
        if (plainLen == 0 || plainLen > 250) return false;

        // PKCS#7 padding calculation
        uint8_t padVal = 16 - (plainLen % 16);
        size_t paddedLen = plainLen + padVal;
        size_t authenticatedDataLen = 16 + paddedLen;
        size_t totalRequired = authenticatedDataLen + HMAC_SIZE;

        if (totalRequired > maxOutLen || totalRequired > MAX_ENCRYPTED_PACKET_SIZE) return false;

        uint8_t iv[16];
        generateIV(iv);
        memcpy(outBuffer, iv, 16); // Prepend IV

        // Create temporary buffer for padded data
        uint8_t tempBuf[256];
        memcpy(tempBuf, plainText, plainLen);
        memset(tempBuf + plainLen, padVal, padVal);

        mbedtls_aes_context aes;
        mbedtls_aes_init(&aes);
        mbedtls_aes_setkey_enc(&aes, PRE_SHARED_KEY, 128);

        uint8_t iv_copy[16];
        memcpy(iv_copy, iv, 16); // mbedtls mutates IV during CBC

        int ret = mbedtls_aes_crypt_cbc(&aes, MBEDTLS_AES_ENCRYPT, paddedLen, iv_copy, tempBuf, outBuffer + 16);
        mbedtls_aes_free(&aes);

        if (ret != 0) return false;

        if (!computeHmac(outBuffer, authenticatedDataLen, outBuffer + authenticatedDataLen)) return false;

        outLen = totalRequired;
        return true;
    }

    // Verify HMAC before decrypting AES-128-CBC [IV + ciphertext + HMAC tag].
    static bool decrypt(const uint8_t *inBuffer, size_t inLen, char *outPlain, size_t &outPlainLen, size_t maxOutLen) {
        outPlainLen = 0;
        if (!inBuffer || !outPlain || inLen < (16 + 16 + HMAC_SIZE) || inLen > MAX_ENCRYPTED_PACKET_SIZE) return false;

        size_t authenticatedDataLen = inLen - HMAC_SIZE;
        size_t cipherLen = authenticatedDataLen - 16;
        if (cipherLen == 0 || (cipherLen % 16) != 0 || cipherLen > 256) return false;

        uint8_t expectedTag[HMAC_SIZE];
        if (!computeHmac(inBuffer, authenticatedDataLen, expectedTag) ||
            !tagsMatch(expectedTag, inBuffer + authenticatedDataLen, HMAC_SIZE)) return false;

        uint8_t iv[16];
        memcpy(iv, inBuffer, 16);

        const uint8_t *cipherData = inBuffer + 16;

        uint8_t tempBuf[256];
        mbedtls_aes_context aes;
        mbedtls_aes_init(&aes);
        mbedtls_aes_setkey_dec(&aes, PRE_SHARED_KEY, 128);

        int ret = mbedtls_aes_crypt_cbc(&aes, MBEDTLS_AES_DECRYPT, cipherLen, iv, cipherData, tempBuf);
        mbedtls_aes_free(&aes);

        if (ret != 0) return false;

        // PKCS#7 unpadding
        uint8_t padVal = tempBuf[cipherLen - 1];
        if (padVal == 0 || padVal > 16) return false; // Invalid padding (tampered or wrong key)

        for (size_t i = 0; i < padVal; i++) {
            if (tempBuf[cipherLen - 1 - i] != padVal) return false;
        }

        size_t actualLen = cipherLen - padVal;
        if (actualLen >= maxOutLen) return false;

        memcpy(outPlain, tempBuf, actualLen);
        outPlain[actualLen] = '\0';
        outPlainLen = actualLen;
        return true;
    }

    // Validate Community Credential
    static bool verifyCommunityCredential(const char *credential) {
        if (!credential) return false;
        return (strcmp(credential, COMMUNITY_ACCESS_CREDENTIAL) == 0);
    }

    static bool authenticateFrame(const uint8_t *data, size_t dataLen, uint8_t *tag) {
        if (!data || !tag) return false;
        return computeHmac(data, dataLen, tag);
    }

    static bool verifyFrame(const uint8_t *data, size_t dataLen, const uint8_t *tag) {
        if (!data || !tag) return false;
        uint8_t expectedTag[HMAC_SIZE];
        if (!computeHmac(data, dataLen, expectedTag)) return false;
        bool matches = tagsMatch(expectedTag, tag, HMAC_SIZE);
        memset(expectedTag, 0, sizeof(expectedTag));
        return matches;
    }
};

#endif
