#!/usr/bin/env python3
"""Extract the hidden data from congratulations.tiff pixels"""
from PIL import Image

imtiff = Image.open('congratulations.tiff')
(width, height) = imtiff.size
imdata = imtiff.getdata()

# A byte is represented by 4 pixels, and there is no data past half the height of the image
databytes = bytearray(width * height // 8)

for pxlpos, pxlvalues in enumerate(imdata):
    if pxlpos >= width * height // 2:
        break
    bytepos = pxlpos // 4
    bitpos_in_byte = 6 - 2 * (pxlpos - 4 * bytepos)
    databytes[bytepos] |= (pxlvalues[0] & 1) << (bitpos_in_byte + 1)
    databytes[bytepos] |= (pxlvalues[1] & 1) << bitpos_in_byte

with open('hidden3.tar.bz2', 'wb') as f:
    f.write(databytes)
