#!/usr/bin/python

from adafruit_thermal import AdafruitThermal
import gfx.adalogo as adalogo
import gfx.adaqrcode as adaqrcode

printer = AdafruitThermal("/dev/ttyUSB0", 9600, timeout=5)

# Test inverse on & off
printer.inverse_on()
printer.println("Inverse ON")
printer.inverse_off()

# Test character double-height on & off
printer.double_height_on()
printer.println("Double Height ON")
printer.double_height_off()

# Set justification (right, center, left) -- accepts 'L', 'C', 'R'
printer.justify('R')
printer.println("Right justified")
printer.justify('C')
printer.println("Center justified")
printer.justify('L')
printer.println("Left justified")

# Test more styles
printer.bold_on()
printer.println("Bold text")
printer.bold_off()

printer.underline_on(1)
printer.println("Underlined text")
printer.underline_off()

printer.underline_on(2)
printer.println("Thick underlined text")
printer.underline_off()

printer.upside_down_on()
printer.println("Upside down text")
printer.upside_down_off()

printer.double_height_on()
printer.println("Double height text")
printer.double_height_off()

printer.double_width_on()
printer.println("Double width")
printer.double_width_off()

printer.strike_on()
printer.println("Strikethrough text")
printer.strike_off()

printer.set_size('L')   # Set type size, accepts 'S', 'M', 'L'
printer.println("Large")
printer.set_size('M')
printer.println("Medium")
printer.set_size('S')
printer.println("Small")

printer.justify('C')
printer.println("normal\nline\nspacing")
printer.set_line_height(50)
printer.println("Taller\nline\nspacing")
printer.set_line_height()  # Reset to default
printer.justify('L')

hasPaper = str(printer.has_paper())
print("Does the printer have paper? " + hasPaper)
printer.println("Does the printer have paper? " + hasPaper)

# Barcode examples
printer.feed(1)
# CODE39 is the most common alphanumeric barcode
printer.print_barcode("ADAFRUT", printer.CODE39)
printer.set_barcode_height(100)
# Print UPC line on product barcodes
printer.print_barcode("123456789123", printer.UPC_A)

# Print the 75x75 pixel logo in adalogo.py
printer.print_bitmap(adalogo.width, adalogo.height, adalogo.data)

# Print the 135x135 pixel QR code in adaqrcode.py
printer.print_bitmap(adaqrcode.width, adaqrcode.height, adaqrcode.data)
printer.println("Adafruit!")
printer.feed(2)

printer.sleep()       # Tell printer to sleep
printer.wake()        # Call wake() before printing again, even if reset
printer.set_default()  # Restore printer to defaults
