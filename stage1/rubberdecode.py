#!/usr/bin/env python3
"""Decode the Rubber Ducky inject.bin compiled script"""
import struct
import sys

# Build a (opcode, modifier)-to-char dictonary
OM2C = {
    (0x1e, 0): '1', (0x1e, 2): '!',
    (0x1f, 0): '2', (0x1f, 2): '@',
    (0x20, 0): '3', (0x20, 2): '#',
    (0x21, 0): '4', (0x21, 2): '$',
    (0x22, 0): '5', (0x22, 2): '%',
    (0x23, 0): '6', (0x23, 2): '^',
    (0x24, 0): '7', (0x24, 2): '&',
    (0x25, 0): '8', (0x25, 2): '*',
    (0x26, 0): '9', (0x26, 2): '(',
    (0x27, 0): '0', (0x27, 2): ')',
    (0x28, 0): '[ENTER]\n', (0x29, 0): '[ESC]\n',
    (0x2b, 0): '\t', (0x2c, 0): ' ',
    (0x2d, 0): '-', (0x2d, 2): '_',
    (0x2e, 0): '=', (0x2e, 2): '+',
    (0x2f, 0): '[', (0x2f, 2): '{',
    (0x30, 0): ']', (0x30, 2): '}',
    (0x31, 0): '\\', (0x31, 2): '|',
    (0x33, 0): ':', (0x33, 2): ';',
    (0x34, 0): "'", (0x34, 2): '"',
    (0x35, 0): '`', (0x35, 2): '~',
    (0x36, 0): ',', (0x36, 2): '<',
    (0x37, 0): '.', (0x37, 2): '>',
    (0x38, 0): '/', (0x38, 2): '?',
}
# Alphabet
for i in range(26):
    OM2C[(i + 4, 0)] = chr(ord('a') + i)
    OM2C[(i + 4, 2)] = chr(ord('A') + i)

delay_time = 0
with open('inject.bin', 'rb') as f:
    while True:
        injectdata = f.read(2)
        if len(injectdata) == 0:
            break
        opcode, modifier = struct.unpack('BB', injectdata)

        # "DELAY" is encoded with successive opcode-0 commands
        if opcode == 0:
            delay_time += modifier
            continue
        if delay_time:
            print("[DELAY {}]".format(delay_time))
            delay_time = 0

        # WIN key + letter is encoded with modifier 8
        if modifier & 8:
            c = OM2C.get((opcode, modifier & ~8))
            if c is not None:
                print("[WIN {}]".format(c))
                continue

        sys.stdout.write(OM2C.get((opcode, modifier)))
