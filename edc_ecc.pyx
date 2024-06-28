# cython: language_level=3

cdef:
    unsigned char ecc_f_lut[256]
    unsigned char ecc_b_lut[256]
    unsigned int edc_lut[256]

cpdef __cinit__():
    cdef unsigned int i, j, edc
    for i in range(256):
        j = (i << 1) ^ (0x11D if i & 0x80 else 0)
        ecc_f_lut[i] = j
        ecc_b_lut[i ^ j] = i
        edc = i
        for j in range(8):
            edc = (edc >> 1) ^ (0xD8018001 if edc & 1 else 0)
        edc_lut[i] = edc

__cinit__()

cpdef unsigned int ComputeEdcBlockPartial(unsigned int edc, const unsigned char *src, size_t length):
    cdef size_t i
    for i in range(length):
        edc = (edc >> 8) ^ edc_lut[(edc ^ src[i]) & 0xFF]
    return edc

cpdef bytes ComputeEdcBlock(const unsigned char *src, size_t length):
    cdef unsigned int edc = ComputeEdcBlockPartial(0, src, length)
    return bytes([(edc >> 0) & 0xFF, (edc >> 8) & 0xFF, (edc >> 16) & 0xFF, (edc >> 24) & 0xFF])

cpdef bytes ComputeEccBlock(const unsigned char *src, unsigned int major_count, unsigned int minor_count, unsigned int major_mult, unsigned int minor_inc):
    cdef:
        unsigned int len = major_count * minor_count
        unsigned int major, minor, index
        unsigned char address[4]
        unsigned char ecc_a, ecc_b, temp
        unsigned char dest[256]

    for major in range(major_count):
        index = (major >> 1) * major_mult + (major & 1)
        ecc_a = 0
        ecc_b = 0
        address[:4] = b'\x00\x00\x00\x00'

        for minor in range(minor_count):
            if index < 4:
                temp = address[index]
            else:
                temp = src[index - 4]

            index += minor_inc

            if index >= len:
                index -= len

            ecc_a ^= temp
            ecc_b ^= temp
            ecc_a = ecc_f_lut[ecc_a]

        ecc_a = ecc_b_lut[ecc_f_lut[ecc_a] ^ ecc_b]
        dest[major] = ecc_a
        dest[major + major_count] = ecc_a ^ ecc_b
    return bytes([dest[i] for i in range(major_count * 2)])
