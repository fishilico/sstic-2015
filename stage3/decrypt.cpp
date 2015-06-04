#include <cryptopp/serpent.h>
#include <cryptopp/modes.h>
#include <cryptopp/filters.h>
#include <fstream>
#include <iostream>

int main()
{
    const unsigned char key[32] = {
        0x66, 0xc1, 0xba, 0x5e, 0x8c, 0xa2, 0x9a, 0x8a, 0xb6, 0xc1, 0x05, 0xa9,
        0xbe, 0x9e, 0x75, 0xfe, 0x0b, 0xa0, 0x79, 0x97, 0xa8, 0x39, 0xff, 0xea,
        0xe9, 0x70, 0x0b, 0x00, 0xb7, 0x26, 0x9c, 0x8d
    };
    const unsigned char iv[16] = {
        0x53, 0x53, 0x54, 0x49, 0x43, 0x32, 0x30, 0x31, 0x35, 0x2d, 0x53, 0x74,
        0x61, 0x67, 0x65, 0x33
    };

    /* Read encrypted */
    std::ifstream encrypted_file("encrypted", std::ios::in|std::ios::binary);
    char enc_data[296798];
    encrypted_file.read(enc_data, sizeof(enc_data));
    encrypted_file.close();
    std::string encrypted(enc_data, sizeof(enc_data));

    /* Decrypt with Serpent-1-CBC-With-CTS */
    CryptoPP::CBC_CTS_Mode<CryptoPP::Serpent>::Decryption decipher;
    decipher.SetKeyWithIV(key, sizeof(key), iv, sizeof(iv));
    std::string decrypted;
    CryptoPP::StringSource ss(
        encrypted, true, 
        new CryptoPP::StreamTransformationFilter(decipher, new CryptoPP::StringSink(decrypted))
    );

    /* Write decrypted */
    std::ofstream decrypted_file("decrypted", std::ios::out|std::ios::binary|std::ios::trunc);
    decrypted_file << decrypted;
    decrypted_file.close();
    return 0;
}
