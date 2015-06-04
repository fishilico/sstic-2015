#!/usr/bin/env python3
"""Extract the data from the sTic sections of congratulations.png"""
import struct
import zlib

with open('congratulations.png', 'rb') as f:
    pngdata = f.read()

offset = 0x5b
hiddendata = b''
while True:
    length, chunktype = struct.unpack('>II', pngdata[offset:offset + 8])

    # Stop when the chunk type is no longer "sTic"
    if chunktype != 0x73546963:
        break
    hiddendata += pngdata[offset + 8:offset + 8 + length]
    offset += 12 + length

with open('hidden2.tar.bz2', 'wb') as f:
    f.write(zlib.decompress(hiddendata))
