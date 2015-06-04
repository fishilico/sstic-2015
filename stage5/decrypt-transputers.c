#include <stdint.h>
#include <string.h>

void decrypt(const uint8_t argkey[12], const uint8_t *src, uint8_t *dst, uint32_t size)
{
    /* Local state of each transputer which uses one */
    uint8_t trans4w1 = 0, trans5w1 = 0;
    uint16_t trans6w1 = 0;
    uint8_t trans8w4 = 0, trans8w5sums[4] = {};
    uint8_t trans10w2 = 0, trans10w4buff0[4] = {}, trans10w4buffers[4 * 12] = {};
    uint8_t trans11next = 0;

    uint32_t byteidx;
    uint8_t key[12], i;

    /* Copy the key in a local buffer which is modified */
    memcpy(key, argkey, 12);

    /* Initialize transputer 6 state with the initial key buffer */
    for (i = 0; i < 12; i++)
        trans6w1 += key[i];

    for (byteidx = 0; byteidx < size; byteidx++) {
        const uint32_t keyidx = byteidx % 12;
        uint8_t transres, s0_5 = 0, s6_11 = 0, s0_11, s_t10 = 0;

        /* Decrypt one byte (code in transputer 0) */
        *(dst++) = *(src++) ^ (keyidx + 2 * key[keyidx]);

        /* Compute sums of key[0] to key[5], key[6] to key[11]... */
        for (i = 0; i < 6; i++)
            s0_5 += key[i];
        for (i = 6; i < 12; i++)
            s6_11 += key[i];
        /* ... and from key[0] to key[11] */
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

        /* Transputer 10 sum */
        for (i = 0; i < 4; i++)
            s_t10 += trans10w4buff0[i];
        transres ^= trans10w4buffers[12 * (s_t10 & 3) + ((s_t10 >> 4) % 12)];

        /* Transputer 0 combines the results for all transputers into one byte of the key */
        key[keyidx] = transres;
    }
}
