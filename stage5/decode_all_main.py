#!/usr/bin/env python3
"""Decode the main program which is run on transputers 4 to 12"""
import sys
sys.path.insert(0, '.')
from decode_st20 import FileMeta

CODE_LABELS = {
    4: {
        0x33: 'mainloop',
        0x3e: 'forloop',
        0x55: 'forloop_end',
        },
    5: {
        0x33: 'mainloop',
        0x3e: 'forloop_W[0]=0..11',
        0x55: 'forloop_end',
    },
    6: {
        0x33: 'mainloop',
        0x42: 'forloop_W[0]=0..11',
        0x59: 'forloop_end',
        0x5b: 'endif',
    },
    7: {
        0x2f: 'mainloop',
        0x3e: 'forloop_W[0]=0..6',
        0x5e: 'forloop_end',
    },
    8: {
        0x33: 'init_forloop1_W[2]=0..3',
        0x35: 'init_forloop2_W[0]=0..11',
        0x48: 'init_forloop2_end',
        0x51: 'mainloop',
        0x69: '_0x80001069',
        0x6f: 'forloop1_W[2]=0..3',
        0x73: 'forloop2_W[0]=0..11',
        0x8c: 'forloop2_end',
        0xa1: 'forloop1_end',
    },
    9: {
        0x2f: 'mainloop',
        0x3e: 'forloop_W[0]=0..11',
        0x5b: 'forloop_end',
    },
    10: {
        0x33: 'init_forloop1_W[0]=0..3',
        0x35: 'init_forloop2_W[1]=0..11',
        0x48: 'init_forloop2_end',
        0x51: 'mainloop',
        0x69: 'endif',
        0x6d: 'forloop_W[0]=0..4',
        0x84: 'forloop_end',
    },
    11: {
        0x31: 'mainloop',
    },
    12: {
        0x33: 'fill_W[3,4,5]_with_zeros',
        0x42: 'mainloop',
    }
}

for i in range(4, 13):
    print("\n---------------- [ TRANSPUTER {}] ----------------".format(i))
    with open('transputer{}_main.bin'.format(i), 'rb') as f:
        fw = f.read().rstrip(b' ')

    code_labels = CODE_LABELS.get(i, {})
    code_labels[0x1f] = 'recv(chan=B, mem=C, len=W[0])'
    code_labels[0x25] = 'send(chan=B, mem=C, len=W[0])'
    code_labels[0x2b] = 'entry'
    comments = {}

    FileMeta(fw, 0x1f, code_labels, {}, comments).show_all()
