#!/usr/bin/env python3
"""Decode the firmware of transputer 0"""
import sys
sys.path.insert(0, '.')
from decode_st20 import FileMeta

CODE_LABELS = {
    0x00: 'boot',
    0x17: 'initialize_other_transputers',
    0x37: 'initialization_done',
    0x77: 'mainloop',
    0xf4: 'end',
}

DATA_LABELS = {
    0xdc: '"Boot ok"',
    0xe4: '"Code Ok"',
    0xec: '"Decrypt"',
}

COMMENTS = {
    0x54: "read 'KEY:'",
    0xcf: "W[4] is incremented modulo 12",
}

with open('input.bin', 'rb') as f:
    inputdata = f.read()

# First byte if the size of the firmware
fwsize = inputdata[0]
fw = inputdata[1:1 + fwsize]
FileMeta(fw, 0, CODE_LABELS, DATA_LABELS, COMMENTS).show_all()
