#!/usr/bin/python

import gfx.adalogo as adalogo
import gfx.adaqrcode as adaqrcode
from adafruit_thermal import AdafruitThermal
from enums import Barcode

printer = AdafruitThermal("/dev/serial0", 9600, timeout=5)


def test_sizes():
    printer.set_size("L")  # Set type size, accepts "S", "M", "L"
    printer.println("Large")
    printer.set_size("M")
    printer.println("Medium")
    printer.set_size("S")
    printer.println("Small")


# Test inverse on & off
printer.inverse(True)
printer.println("Inverse ON")
printer.inverse(False)

# Test sideways mode
printer.rotate_sideways(True)
printer.println("Sideways mode ON")
printer.rotate_sideways(False)

# Test small font
printer.small_font(True)
printer.println("Small font ON")
test_sizes()
printer.small_font(False)

# Set justification (right, center, left) -- accepts "L", "C", "R"
printer.justify("R")
printer.println("Right justified")
printer.justify("C")
printer.println("Center justified")
printer.justify("L")
printer.println("Left justified")

# Test more styles
printer.bold(True)
printer.println("Bold text")
printer.bold(False)

printer.underline(1)
printer.println("Underlined text")
printer.underline(2)
printer.println("Thick underlined text")
printer.underline(0)

printer.upside_down(True)
printer.println("Upside down text")
printer.upside_down(False)

printer.double_height(True)
printer.println("Double height text")
printer.double_height(False)

printer.double_width(True)
printer.println("Double width")
printer.double_width(False)

printer.strikethrough(True)
printer.println("Strikethrough text")
printer.strikethrough(False)

test_sizes()

printer.justify("C")
printer.println("normal\nline\nspacing")
printer.set_line_height(50)
printer.println("Taller\nline\nspacing")
printer.set_line_height()  # Reset to default
printer.justify("L")

hasPaper = str(printer.has_paper())
print("Does the printer have paper? " + hasPaper)
printer.println("Does the printer have paper? " + hasPaper)

input("Remove the paper and press enter. ")
hasPaper = str(printer.has_paper())
print("Does the printer have paper? " + hasPaper)
input("Put the paper back and press enter. ")

# Barcode examples
printer.feed(1)
# CODE39 is the most common alphanumeric barcode
printer.print_barcode("ADAFRUT", Barcode.CODE39)
printer.set_barcode_height(100)
# Print UPC line on product barcodes
printer.print_barcode("123456789123", Barcode.UPC_A)

# Print the 75x75 pixel logo in adalogo.py
printer.print_bitmap(adalogo.width, adalogo.height, adalogo.data)

# Print the 135x135 pixel QR code in adaqrcode.py
printer.print_bitmap(adaqrcode.width, adaqrcode.height, adaqrcode.data)
printer.println("Adafruit!")
printer.feed(2)

printer.sleep()  # Tell printer to sleep
printer.wake()  # Call wake() before printing again, even if reset
printer.set_default()  # Restore printer to defaults
