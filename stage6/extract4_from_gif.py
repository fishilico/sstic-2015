#!/usr/bin/env python3
"""Modify congratulations.gif to show the solution"""
from PIL import Image

imgif = Image.open('congratulations.gif')
palette = imgif.getpalette()
palette[6:9] = [181, 230, 255]
imgif.putpalette(palette)
imgif.save('solution.png')
