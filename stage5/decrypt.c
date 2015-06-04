/**
 * Decrypt congratulations.tar.bz2.enc by bruteforcing the key
 * Compile with: gcc -Wall -Wextra -O3 decrypt.c -o decrypt -lbz2
 */
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include <bzlib.h>

/**
 * Transputers code: decrypt size bytes in src to dst using the specified key
 */
static int decrypt(const uint8_t argkey[12], const uint8_t *src, uint8_t *dst, uint32_t size)
{
    uint8_t trans4w1 = 0, trans5w1 = 0;
    uint16_t trans6w1 = 0;
    uint8_t trans8w4 = 0, trans8w5sums[4] = {};
    uint8_t trans10w2 = 0, trans10w4buff0[4] = {}, trans10w4buffers[4 * 12] = {};
    uint8_t trans11next = 0;
    uint32_t byteidx;
    uint8_t key[12], i;

    memcpy(key, argkey, 12);

    for (i = 0; i < 12; i++)
        trans6w1 += key[i];

    for (byteidx = 0; byteidx < size; byteidx++) {
        const uint32_t keyidx = byteidx % 12;
        uint8_t transres, s0_5 = 0, s6_11 = 0, s0_11, s_t10 = 0;

        *(dst++) = *(src++) ^ (keyidx + 2 * key[keyidx]);

        for (i = 0; i < 6; i++)
            s0_5 += key[i];
        for (i = 6; i < 12; i++)
            s6_11 += key[i];
        s0_11 = s0_5 + s6_11;

        trans6w1 =
            ((trans6w1 & 0x8000) >> 15) ^
            ((trans6w1 & 0x4000) >> 14) ^
            ((trans6w1 << 1) & 0xffff);

        trans8w5sums[trans8w4] = s0_11;
        trans8w4 = (trans8w4 + 1) % 4;

        trans10w4buff0[trans10w2] = key[0];
        memcpy(trans10w4buffers + 12 * trans10w2, key, 12);
        trans10w2 = (trans10w2 + 1) % 4;

        transres = (trans6w1 & 0xff) ^ s0_5 ^ s6_11 ^ key[trans11next];
        transres ^= key[(key[0] ^ key[3] ^ key[7]) % 12];
        trans11next = (key[1] ^ key[5] ^ key[9]) % 12;

        for (i = 0; i < 12; i++) {
            uint8_t k = key[i];
            trans4w1 += k;
            trans5w1 ^= k;
            transres ^= k << (i & 7);
        }
        transres ^= trans4w1 ^ trans5w1;

        for (i = 0; i < 4; i++)
            transres ^= trans8w5sums[i];
        for (i = 0; i < 4; i++)
            s_t10 += trans10w4buff0[i];
        transres ^= trans10w4buffers[12 * (s_t10 & 3) + ((s_t10 >> 4) % 12)];

        key[keyidx] = transres;

        /* Destination[14] will be written using key[2] later.
         * Abort early if this byte will be non null for the BZip2 header.
         * Don't abort when decrypting the test vector.
         */
        if (size > 100 && byteidx == 2) {
            const uint8_t *origsrc = src - byteidx - 1;
            uint8_t decrypt14 = (origsrc[14] ^ (2 + 2 * key[2])) & 0xff;
            if (decrypt14 != 0)
                return 0;
        }
    }
    return 1;
}

/**
 * Test decrypt() function with the provided test vector
 */
static int testvector(void)
{
    const uint8_t encrypted[] = {
        0x1d, 0x87, 0xc4, 0xc4, 0xe0, 0xee, 0x40, 0x38, 0x3c, 0x59, 0x44, 0x7f,
        0x23, 0x79, 0x8d, 0x9f, 0xef, 0xe7, 0x4f, 0xb8, 0x24, 0x80, 0x76, 0x6e
    };
    const uint8_t key[] = "*SSTIC-2015*";
    uint8_t decrypted[25];

    decrypt(key, encrypted, decrypted, 24);
    decrypted[24] = '\0';
    printf("%s\n", (char *)decrypted);
    return !strcmp((char *)decrypted, "I love ST20 architecture");
}

int main(int argc, char **argv)
{
#define INPUT_SIZE 250606
    static uint8_t encrypted[INPUT_SIZE];
    static uint8_t decrypted[INPUT_SIZE];
    static uint8_t decompressed[INPUT_SIZE];
    uint8_t key[12];
    const uint8_t bz2head[10] = {
        0x42, 0x5a, 0x68, 0x39, 0x31, 0x41, 0x59, 0x26, 0x53, 0x59
    };
    unsigned int i;
    ssize_t ret_size;
    FILE *f;
    bz_stream bst;
    int bzret, j;

    assert(testvector());

    f = fopen("encrypted", "rb");
    assert(f);
    ret_size = fread(encrypted, 1, INPUT_SIZE, f);
    assert(ret_size == INPUT_SIZE);
    fclose(f);

    /* Initialize key constants from BZip2 header magic */
    for (i = 0; i < sizeof(bz2head); i++) {
        uint8_t wanted = encrypted[i] ^ bz2head[i];
        assert((wanted - i) % 2 == 0);
        key[i] = ((wanted - i) / 2) & 0x7f;
    }

    /* Bruteforce keys, starting with the given integer, if any */
    i = (argc >= 2) ? (unsigned int)atoi(argv[1]) : 0;
    for (; i < 256 * 256 * 1024; i++) {
        /* Choose the most significant bits of 10 first bytes according to i */
        for (j = 0; j < 10; j++) {
            if ((i >> (16 + j)) & 1) {
                key[j] |= 0x80;
            } else {
                key[j] &= 0x7f;
            }
        }
        /* Bytes 10 and 11 can't be known */
        key[10] = (i >> 8) & 0xff;
        key[11] = i & 0xff;

        if (!decrypt(key, encrypted, decrypted, INPUT_SIZE)) {
            /* Decrypt aborted early, so the key is invalid */
            continue;
        }

        /* Test BZ2 data */
        memset(&bst, 0, sizeof(bst));
        bzret = BZ2_bzDecompressInit(&bst, 0, 0);
        assert(bzret == BZ_OK);
        bst.next_in = (char *)decrypted;
        bst.avail_in = sizeof(decrypted);
        bst.next_out = (char *)decompressed;
        bst.avail_out = sizeof(decompressed);
        bzret = BZ2_bzDecompress(&bst);
        BZ2_bzDecompressEnd(&bst);
        if (bzret < 0) {
            /* Invalid data */
            continue;
        }

        /* Key found */
        printf("Found %#04x\n", i);
        printf("Key:");
        for (j = 0; j < 12; j++) {
            printf(" %02x", key[j]);
        }
        printf("\n");

        /* Save the file */
        f = fopen("congratulations.tar.bz2", "wb");
        assert(f != NULL);
        ret_size = fwrite(decrypted, 1, sizeof(decrypted), f);
        assert(ret_size == (ssize_t)sizeof(decrypted));
        fclose(f);
        return 0;
    }
    fprintf(stderr, "Bruteforce failed!\n");
    return 1;
}
