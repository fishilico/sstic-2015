#!/usr/bin/env python3
"""Decode the firmware of transputer 4-12 loader"""
import sys
sys.path.insert(0, '.')
from decode_st20 import FileMeta

CODE_LABELS = {
    0x00: 'boot',
    0x20: 'exit',
}

COMMENTS = {
    0x19: "Download the next code in 0x1f",
    0x1e: "Run the main code",
}

with open('transputer4_loader.bin', 'rb') as f:
    fw = f.read().rstrip(b' ')

FileMeta(fw, 0, CODE_LABELS, {}, COMMENTS).show_all()
