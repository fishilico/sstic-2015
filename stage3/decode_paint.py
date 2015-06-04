#!/usr/bin/env python2
"""Decode the mouse movements in paint.cap"""
from scapy.all import *
from PIL import Image, ImageDraw

class URB(Packet):
    fields_desc = [
        LELongField('URB_id', 0),
        ByteField('URB_type', 0),
        ByteField('URB_transfer_type', 0),
        BitField('URB_direction', 0, 1),
        BitField('URB_endpoint', 0, 7),
        ByteField('URB_device', 0),
        LEShortField('URB_busid', 0),
        ByteField('device_setup_rq', 0),
        ByteField('data_ispresent', 0),
        LELongField('URB_sec', 0),
        LEIntField('URB_usec', 0),
        LEIntField('URB_status', 0),
        LEIntField('URB_length', 0),
        LEIntField('data_length', 0),
        XLongField('UNKNOWN', 0),
        LEIntField('interval', 0),
        LEIntField('start_frame', 0),
        LEIntField('copy_transfer_flags', 0),
        LEIntField('num_iso_desc', 0),
    ]

class SignedByteField(Field):
    def __init__(self, name, default):
        Field.__init__(self, name, default, fmt="b")

class URBMouseInput(Packet):
    fields_desc = [
        ByteField('buttons', 0),
        SignedByteField('rel_x', 0),
        SignedByteField('rel_y', 0),
        SignedByteField('rel_z', 0),
    ]

conf.l2types.register(220, URB)

# List of mouse positions (btn, x, y) relative to the initial position
mousemove_list = []
packets = rdpcap('paint.cap')
x = y = 0
for urbpkt in packets[6:]:  # Skip the first 6 packets
    if urbpkt.data_length == 0:
        continue
    mouse_in = URBMouseInput(urbpkt.payload.load)
    x += mouse_in.rel_x
    y += mouse_in.rel_y
    mousemove_list.append((mouse_in.buttons, x, y))

# Replay the mouse move movements in an image
xmin = min(mm[1] for mm in mousemove_list)
xmax = max(mm[1] for mm in mousemove_list)
ymin = min(mm[2] for mm in mousemove_list)
ymax = max(mm[2] for mm in mousemove_list)
im = Image.new('RGB', (xmax + 1 - xmin, ymax + 1 - ymin), 'white')
draw = ImageDraw.Draw(im)
for btn, x, y in mousemove_list:
    if btn:
        draw.point((x - xmin, y - ymin), fill='black')
im.save('paint-out.png', 'PNG')
