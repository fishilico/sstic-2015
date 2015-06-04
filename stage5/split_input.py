#!/usr/bin/env python3
"""Split input.bin into the several payloads which are sent to transputers"""
import struct

with open('input.bin', 'rb') as f:
    inputdata = f.read()

# Input data starts with the booted firmware
bootlen = inputdata[0]
print("[{:04x}-{:04x}] Transputer 0 code ({} bytes)".format(
    1, bootlen, bootlen))
with open('transputer0.bin', 'wb') as f:
    f.write(inputdata[1:1 + bootlen])

# Then there is a zero-terminated list of packets forwarded to sub-links
offset = 1 + bootlen
level1pkts = {1: [], 2: [], 3: []}
while True:
    # Decode the 12-byte header
    length, destination, _ = struct.unpack('<III', inputdata[offset:offset + 12])
    offset += 12
    if length == 0:
        break
    # destination 0x80000004 is link 1, 0x80000008 is link 2, 0x8000000c link 3
    lnkdst = (destination - 0x80000000) // 4
    assert destination == 0x80000000 + lnkdst * 4
    level1pkts[lnkdst].append((offset, length))
    offset += length

final_offset = offset
print("[{:04x}-{:04x}] Transputer 0 forwarded packets:".format(
    1 + bootlen, final_offset - 1))

for lnkdst in sorted(level1pkts.keys()):
    off_len_list = level1pkts[lnkdst]

    # First payload is main code for transputers 1, 2 and 3
    (offset, length) = off_len_list[0]
    codelen = inputdata[offset]
    assert codelen == length - 1
    print("[{:04x}-{:04x}] * Transputer {} code ({} bytes)".format(
        offset + 1, offset + length - 1, lnkdst, codelen))
    with open('transputer{}.bin'.format(lnkdst), 'wb') as f:
        f.write(inputdata[offset + 1:offset + length])

    # Then forwarded packets
    level2pkts = {1: [], 2: [], 3: []}
    for offset, length in off_len_list[1:]:
        length2, destination, _ = struct.unpack('<III', inputdata[offset:offset + 12])
        assert length2 + 12 == length
        lnkdst2 = (destination - 0x80000000) // 4
        assert destination == 0x80000000 + lnkdst2 * 4
        level2pkts[lnkdst2].append((offset + 12, length2))

    for lnkdst2 in sorted(level2pkts.keys()):
        off_len_list = level2pkts[lnkdst2]

        # First payload is loader code for transputers 4-12
        transputer_id = 3 * lnkdst + lnkdst2
        (offset, length) = off_len_list[0]
        codelen = inputdata[offset]
        assert codelen == length - 1
        print("[{:04x}-{:04x}]   * Transputer {} loader code ({} bytes)".format(
            offset + 1, offset + length - 1, transputer_id, codelen))
        with open('transputer{}_loader.bin'.format(transputer_id), 'wb') as f:
            f.write(inputdata[offset + 1:offset + length])

        # Second payload is main code
        assert len(off_len_list) == 2
        (offset, length) = off_len_list[1]
        length2, _, entry = struct.unpack('<III', inputdata[offset:offset + 12])
        assert length2 + 12 == length
        print("[{:04x}-{:04x}]     * Transputer {} main code ({} bytes), entry {:#x}".format(
            offset + 12, offset + length - 1, transputer_id, length2, entry))
        with open('transputer{}_main.bin'.format(transputer_id), 'wb') as f:
            f.write(inputdata[offset + 12:offset + length])

offset = final_offset

# Key
print("[{:04x}-{:04x}] '{}'".format(
    offset, offset + 3, inputdata[offset:offset + 4].decode('ascii')))
print("[{:04x}-{:04x}] {}".format(
    offset + 4, offset + 15, repr(inputdata[offset + 4:offset + 16])))
offset += 16

# Name
namelen = inputdata[offset]
name = inputdata[offset + 1:offset + 1 + namelen].decode('ascii')
print("[{:04x}-{:04x}] Name: '{}'".format(offset, offset + namelen, name))
offset += 1 + namelen

# Encrypted data
print("[{:04x}-{:04x}] Encrypted data ({} bytes)".format(
    offset, len(inputdata) - 1, len(inputdata) - offset))

with open('encrypted', 'wb') as f:
    f.write(inputdata[offset:])
