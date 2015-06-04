#!/usr/bin/env python3
"""Decode the firmware shared between transputers 1, 2 and 3"""
import sys
sys.path.insert(0, '.')
from decode_st20 import FileMeta

CODE_LABELS = {
    0x00: 'boot',
    0x0b: 'relay_code',
    0x26: 'mainloop',
    0x6d: 'exit',
}

with open('transputer1.bin', 'rb') as f:
    fw = f.read().rstrip(b' ')

FileMeta(fw, 0, CODE_LABELS, {}, {}).show_all()
