#!/usr/bin/python
#
# Thermal calibration utility for adafruit_thermal Python library.
# Run this utility before using the printer for the first time, any
# time a different power supply is used, or when using paper from a
# different source.
#
# Prints a series of black bars with increasing "heat time" settings.
# Because printed sections have different "grip" characteristics than
# blank paper, as this progresses the paper will usually at some point
# jam -- either uniformly, making a short bar, or at one side or the
# other, making a wedge shape.  In some cases, the Pi may reset for
# lack of power.
#
# Whatever the outcome, take the last number printed BEFORE any
# distorted bar and enter in in adafruit_thermal.py as default_heat_time
# (around line 61).
#
# You may need to pull on the paper as it reaches the jamming point,
# and/or just abort the program, press the feed button and take the
# last good number.

from __future__ import print_function

from adafruit_thermal import AdafruitThermal
from enums import Barcode

printer = AdafruitThermal("/dev/serial0", 9600)

for i in range(0, 256, 15):
    printer.set_heat_time(i)
    printer.println(i)  # Print heat time
    printer.set_barcode_height(20)
    printer.print_barcode("ABCDEFGH", Barcode.CODE128)
    # printer.inverse(True)
    # printer.println("                              ", False, False)  # Print 32 spaces (inverted)
    # printer.inverse(False)

printer.set_heat_time()  # Reset heat time to default
printer.feed(4)
