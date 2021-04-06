"""This is a Python library for the Adafruit Thermal Printer.
Pick one up at --> http://www.adafruit.com/products/597
These printers use TTL serial to communicate, 2 pins are required.
IMPORTANT: On 3.3V systems (e.g. Raspberry Pi), use a 10K resistor on
the RX pin (TX on the printer, green wire), or simply leave unconnected.

Adafruit invests time and resources providing this open source code.
Please support Adafruit and open-source hardware by purchasing products
from Adafruit!

Written by Limor Fried/Ladyada for Adafruit Industries.
Python port by Phil Burgess for Adafruit Industries.
MIT license, all text above must be included in any redistribution.
*************************************************************************

This is pretty much a 1:1 direct Python port of the Adafruit_Thermal
library for Arduino.  All methods use the same naming conventions as the
Arduino library, with only slight changes in parameter behavior where
needed.  This should simplify porting existing Adafruit_Thermal-based
printer projects to Raspberry Pi, BeagleBone, etc.  See printertest.py
for an example.

One significant change is the addition of the print_image() function,
which ties this to the Python Imaging Library and opens the door to a
lot of cool graphical stuff!

TO DO:
- Might use standard ConfigParser library to put thermal calibration
  settings in a global configuration file (rather than in the library).
- Make this use proper Python library installation procedure.
- Trap errors properly.  Some stuff just falls through right now.
- Add docstrings throughout!
"""

import math
import pathlib
import textwrap
import time
from typing import Any, BinaryIO, Union

from PIL import Image
from serial import Serial

from enums import Barcode, Charset, Codepage, PrintMode


class AdafruitThermal(Serial):
    """Represents the thermal printer."""

    resume_time = 0.0
    byte_time = 0.0
    dot_print_time = 0.0
    dot_feed_time = 0.0
    prev_byte = "\n"
    column = 0
    max_column = 32
    char_height = 24
    line_spacing = 8
    barcode_height = 50
    print_mode = 0
    default_heat_time = 120
    firmware_version = 268
    sideways = False
    alt_font = False

    def __init__(self, port: str, baudrate: int, *args, **kwargs):
        """Initialise the printer.

        :param port: the port of the printer
        :type port: str
        :param baudrate: the baudrate of the printer
        :type baudrate: int
        """

        # Firmware is assumed version 2.68.  Can override this
        # with the "firmware=X" argument, where X is the major
        # version number * 100 + the minor version number (e.g.
        # pass "firmware=264" for version 2.64.
        self.firmware_version = kwargs.get("firmware", 268)

        # Calculate time to issue one byte to the printer.
        # 11 bits (not 8) to accommodate idle, start and
        # stop bits.  Idle time might be unnecessary, but
        # erring on side of caution here.
        self.byte_time = 11.0 / float(baudrate)

        Serial.__init__(self, port, baudrate, *args, **kwargs)

        # The printer can't start receiving data immediately upon
        # power up -- it needs a moment to cold boot and initialize.
        # Allow at least 0.5 sec of uptime before printer can receive data.
        self.timeout_set(0.5)

        self.wake()
        self.reset()

        # Description of print settings from p. 23 of manual:
        # ESC 7 n1 n2 n3 Setting Control Parameter Command
        # Decimal: 27 55 n1 n2 n3
        # max heating dots, heating time, heating interval
        # n1 = 0-255 Max heat dots, Unit (8dots), Default: 7 (64 dots)
        # n2 = 3-255 Heating time, Unit (10us), Default: 80 (800us)
        # n3 = 0-255 Heating interval, Unit (10us), Default: 2 (20us)
        # The more max heating dots, the more peak current
        # will cost when printing, the faster printing speed.
        # The max heating dots is 8*(n1+1).  The more heating
        # time, the more density, but the slower printing
        # speed.  If heating time is too short, blank page
        # may occur.  The more heating interval, the more
        # clear, but the slower printing speed.

        heat_time = kwargs.get("heattime", self.default_heat_time)
        self.write_bytes(
            27,  # Esc
            55,  # 7 (print settings)
            11,  # Heat dots
            heat_time,  # Lib default
            40)  # Heat interval

        # Description of print density from p. 23 of manual:
        # DC2 # n Set printing density
        # Decimal: 18 35 n
        # D4..D0 of n is used to set the printing density.
        # Density is 50% + 5% * n(D4-D0) printing density.
        # D7..D5 of n is used to set the printing break time.
        # Break time is n(D7-D5)*250us.
        # (Unsure of default values -- not documented)

        print_density = 10  # 100%
        print_break_time = 2  # 500 uS

        self.write_bytes(
            18,  # DC2
            35,  # Print density
            (print_break_time << 5) | print_density)
        self.dot_print_time = 0.03
        self.dot_feed_time = 0.0021

    def timeout_set(self, duration: float):
        """Sets the estimated completion time for a just-issued task.

        Because there's no flow control between the printer and
        computer, special care must be taken to avoid overrunning the
        printer's buffer.

        Serial output is throttled based on serial speed as well as an
        estimate of the device's print and feed rates (relatively slow,
        being bound to moving parts and physical reality).

        After an operation is issued to the printer (e.g. bitmap print),
        a timeout is set before which any other printer operations will
        be suspended.

        This is generally more efficient than using a delay in that it
        allows the calling code to continue with other duties (e.g.
        receiving or decoding an image) while the printer physically
        completes the task.

        :param duration: how long to wait in seconds
        :type duration: float
        """

        self.resume_time = time.time() + duration

    def timeout_wait(self):
        """Waits (if necessary) for the prior task to complete."""

        while (time.time() - self.resume_time) < 0:
            pass

    def set_times(self, print_time: int, feed_time: int) -> None:
        """Set the print and feed times.

        Printer performance may vary based on the power supply
        voltage, thickness of paper, phase of the moon and other
        seemingly random variables.

        This method sets the times (in microseconds) for the paper to
        advance one vertical 'dot' when printing and feeding.

        For example, in the default initialized state, normal-sized text
        is 24 dots tall and the line spacing is 32 dots, so the time for
        one line to be issued is approximately (24 * print time) +
        (8 * feed time).

        The default print and feed times are based on a random test
        unit, but as stated above your reality may be influenced by many
        factors.

        This lets you tweak the timing to avoid excessive delays and/or
        overrunning the printer buffer.

        :param print_time: the print time in seconds
        :type print_time: int
        :param feed_time: the feed time in seconds
        :type feed_time: int
        """

        # Units are in microseconds for
        # compatibility with Arduino library
        self.dot_print_time = print_time / 1000000.0
        self.dot_feed_time = feed_time / 1000000.0

    def write_bytes(self, *args):
        """Write raw bytes.

        :param args: the bytes to write
        :type args: Tuple[Any, ...]
        """

        for arg in args:
            self.timeout_wait()
            self.timeout_set(len(args) * self.byte_time)
            super(AdafruitThermal, self).write(bytes([arg]))

    def write(self, *data):
        """Write bytes.

        This overrides Serial.write() to keep track of paper feed.

        :param data: the bytes to write
        :type data: Tuple[Any, ...]
        """

        for i in range(len(data)):
            c = data[i]
            if c != 0x13:
                self.timeout_wait()
                super(AdafruitThermal, self).write(c)
                d = self.byte_time
                if ((c == "\n") or
                        (self.column == self.max_column)):
                    # Newline or wrap
                    if self.prev_byte == "\n":
                        # Feed line (blank)
                        d += ((self.char_height +
                               self.line_spacing) *
                              self.dot_feed_time)
                    else:
                        # Text line
                        d += ((self.char_height *
                               self.dot_print_time) +
                              (self.line_spacing *
                               self.dot_feed_time))
                        self.column = 0
                        # Treat wrap as newline
                        # on next pass
                        c = "\n"
                else:
                    self.column += 1
                self.timeout_set(d)
                self.prev_byte = c

    def set_heat_time(self, heat_time: int = default_heat_time):
        """Sets the heat time.

        Was previously begin().

        :param heat_time: the heat time to set
        :type heat_time: int, optional
        """
        self.write_bytes(
            27,  # Esc
            55,  # 7 (print settings)
            11,  # Heat dots
            heat_time,
            40)  # Heat interval

    def reset(self):
        """Resets the printer."""
        self.write_bytes(27, 64)  # Esc @ = init command
        self.prev_byte = "\n"  # Treat as if prior line is blank
        self.column = 0
        self.max_column = 32
        self.char_height = 24
        self.line_spacing = 6
        self.barcode_height = 50
        if self.firmware_version >= 264:
            # Configure tab stops on recent printers
            self.write_bytes(27, 68)  # Set tab stops
            self.write_bytes(4, 8, 12, 16)  # every 4 columns,
            self.write_bytes(20, 24, 28, 0)  # 0 is end-of-list.

    def set_default(self) -> None:
        """Restores default text formatting."""

        self.online()
        self.inverse(False)
        self.upside_down(False)
        self.double_height(False)
        self.double_width(False)
        self.strikethrough(False)
        self.bold(False)
        self.rotate_sideways(False)
        self.small_font(False)
        self.justify("L")
        self.set_size("S")
        self.underline(0)
        self.set_barcode_height()
        self.set_charset()
        self.set_code_page()

    def test(self):
        self.write("Hello world!".encode("cp437", "ignore"))
        self.feed(2)

    def test_page(self):
        self.write_bytes(18, 84)
        self.timeout_set(
            self.dot_print_time * 24 * 26 +
            self.dot_feed_time * (6 * 26 + 30))

    def set_barcode_height(self, height: int = 50) -> None:
        """Set the height of the barcode in pixels.

        :param height: the height of the barcode in pixels
        :type height: int, optional
        """

        if height < 1:
            raise ValueError("Barcode height must not be less than 1.")
        self.barcode_height = height
        self.write_bytes(29, 104, height)

    def print_barcode(self, text: str, style: Barcode) -> None:
        """Prints a barcode.

        :param text: the text to encode in the barcode
        :type text: str
        :param style: the style (or type) of the barcode to use
        :type style: Barcode
        :raises TypeError: if the barcode style isn't supported
        """

        new_dict = {  # UPC codes & values for firmware_version >= 264
            Barcode.UPC_A: 65,
            Barcode.UPC_E: 66,
            Barcode.EAN13: 67,
            Barcode.EAN8: 68,
            Barcode.CODE39: 69,
            Barcode.ITF: 70,
            Barcode.CODABAR: 71,
            Barcode.CODE93: 72,
            Barcode.CODE128: 73,
            Barcode.I25: -1,  # NOT IN NEW FIRMWARE
            Barcode.CODEBAR: -1,
            Barcode.CODE11: -1,
            Barcode.MSI: -1
        }
        old_dict = {  # UPC codes & values for firmware_version < 264
            Barcode.UPC_A: 0,
            Barcode.UPC_E: 1,
            Barcode.EAN13: 2,
            Barcode.EAN8: 3,
            Barcode.CODE39: 4,
            Barcode.I25: 5,
            Barcode.CODEBAR: 6,
            Barcode.CODE93: 7,
            Barcode.CODE128: 8,
            Barcode.CODE11: 9,
            Barcode.MSI: 10,
            Barcode.ITF: -1,  # NOT IN OLD FIRMWARE
            Barcode.CODABAR: -1
        }

        # Get the code for the barcode
        if self.firmware_version >= 264:
            n = new_dict[style]
        else:
            n = old_dict[style]
        if n == -1:
            raise TypeError("Barcode %s is not supported in firmware %d." %
                            (style.name, self.firmware_version))

        self.feed()  # Recent firmware requires this?
        self.write_bytes(
            29, 72, 2,  # Print label below barcode
            29, 119, 3,  # Barcode width
            29, 107, n)  # Barcode type
        self.timeout_wait()
        self.timeout_set((self.barcode_height + 40) * self.dot_print_time)

        # Print string
        if self.firmware_version >= 264:
            # Recent firmware: write length byte + string sans NUL
            n = len(text)
            if n > 255:
                n = 255
            super(AdafruitThermal, self).write((chr(n)).encode("utf-8", "ignore"))
            for i in range(n):
                super(AdafruitThermal,
                      self).write(text[i].encode("utf-8", "ignore"))
        else:
            # Older firmware: write string + NUL
            super(AdafruitThermal, self).write(text.encode("utf-8", "ignore"))
        self.prev_byte = "\n"

    def set_print_mode(self, mask: PrintMode) -> None:
        """Set a print mode.

        :param mask: the print mode to set
        :type mask: PrintMode
        """
        self.print_mode |= mask.value
        self.write_print_mode()
        if self.print_mode & PrintMode.DOUBLE_HEIGHT_MASK.value:
            self.char_height = 48
        else:
            self.char_height = 24
        if self.print_mode & PrintMode.DOUBLE_WIDTH_MASK.value:
            if self.alt_font is False:
                self.max_column = 16
            else:
                self.max_column = 21
        else:
            if self.alt_font is False:
                self.max_column = 32
            else:
                self.max_column = 42

    def unset_print_mode(self, mask: PrintMode) -> None:
        """Unset a print mode.

        :param mask: the print mode to unset
        :type mask: PrintMode
        """

        self.print_mode &= ~mask.value
        self.write_print_mode()
        if self.print_mode & PrintMode.DOUBLE_HEIGHT_MASK.value:
            self.char_height = 48
        else:
            self.char_height = 24
        if self.print_mode & PrintMode.DOUBLE_WIDTH_MASK.value:
            if self.alt_font is False:
                self.max_column = 16
            else:
                self.max_column = 21
        else:
            if self.alt_font is False:
                self.max_column = 32
            else:
                self.max_column = 42

    def write_print_mode(self):
        """Write the current print mode."""

        self.write_bytes(27, 33, self.print_mode)

    def inverse(self, mode: bool) -> None:
        """Enables or disables inverse text.

        :param mode: True for on, False for off
        :type mode: bool
        :raises TypeError: if mode is not True or False
        """

        if mode is True:
            self.write_bytes(29, 66, 1)
        elif mode is False:
            self.write_bytes(29, 66, 0)
        else:
            raise TypeError("Inverse mode must be True or False.")

    def upside_down(self, mode: bool) -> None:
        """Enables or disables upside down text.

        :param mode: True for on, False for off
        :type mode: bool
        :raises TypeError: if mode is not True or False
        """

        if mode is True:
            self.set_print_mode(PrintMode.UPDOWN_MASK)
        elif mode is False:
            self.unset_print_mode(PrintMode.UPDOWN_MASK)
        else:
            raise TypeError("Upside down mode must be True or False.")

    def double_height(self, mode: bool) -> None:
        """Enables or disables double height text.

        :param mode: True for on, False for off
        :type mode: bool
        :raises TypeError: if mode is not True or False
        """

        if mode is True:
            self.set_print_mode(PrintMode.DOUBLE_HEIGHT_MASK)
        elif mode is False:
            self.unset_print_mode(PrintMode.DOUBLE_HEIGHT_MASK)
        else:
            raise TypeError("Double height mode must be True or False.")

    def double_width(self, mode: bool) -> None:
        """Enables or disables double width text.

        :param mode: True for on, False for off
        :type mode: bool
        :raises TypeError: if mode is not True or False
        """

        if mode is True:
            self.set_print_mode(PrintMode.DOUBLE_WIDTH_MASK)
        elif mode is False:
            self.unset_print_mode(PrintMode.DOUBLE_WIDTH_MASK)
        else:
            raise TypeError("Double width mode must be True or False.")

    def strikethrough(self, mode: bool) -> None:
        """Enables or disables strikethrough text.

        :param mode: True for on, False for off
        :type mode: bool
        :raises TypeError: if mode is not True or False
        """

        if mode is True:
            self.set_print_mode(PrintMode.STRIKE_MASK)
        elif mode is False:
            self.unset_print_mode(PrintMode.STRIKE_MASK)
        else:
            raise TypeError("Strikethrough mode must be True or False.")

    def bold(self, mode: bool) -> None:
        """Enables or disables bold text.

        :param mode: True for on, False for off
        :type mode: bool
        :raises TypeError: if mode is not True or False
        """

        if mode is True:
            self.set_print_mode(PrintMode.BOLD_MASK)
        elif mode is False:
            self.unset_print_mode(PrintMode.BOLD_MASK)
        else:
            raise TypeError("Bold mode must be True or False.")

    def rotate_sideways(self, mode: bool) -> None:
        """Enables or disables 90 degree rotation clockwise.

        :param mode: True for on, False for off
        :type mode: bool
        :raises TypeError: if mode is not True or False
        """

        if mode is True:
            self.write_bytes(27, 86, 1)
            self.sideways = True
        elif mode is False:
            self.write_bytes(27, 86, 0)
            self.sideways = False
        else:
            raise TypeError("Rotate sideways mode must be True or False.")

    def small_font(self, mode: bool) -> None:
        """Enables or disables the alternative, smaller font.

        :param mode: True for on, False for off
        :type mode: bool
        :raises TypeError: if mode is not True or False
        """

        if mode is True:
            self.set_print_mode(PrintMode.SMALL_FONT_MASK)
            # self.write_bytes(27, 33, 1)
            self.alt_font = True
        elif mode is False:
            self.unset_print_mode(PrintMode.SMALL_FONT_MASK)
            # self.write_bytes(27, 33, 0)
            self.alt_font = False
        else:
            raise TypeError("Small font mode must be True or False.")

    def justify(self, position: str) -> None:
        """Set the text justification.

        L for left.
        C for centre.
        R for right.

        :param position: the justification to use
        :type position: str
        :raises ValueError: if an invalid justification is given
        """

        if position.upper() == "L":
            justify = 0
        elif position.upper() == "C":
            justify = 1
        elif position.upper() == "R":
            justify = 2
        else:
            raise ValueError("Justify position must be L, C, or R.")

        self.write_bytes(0x1B, 0x61, justify)

    def feed(self, lines: int = 1) -> None:
        """Feeds by the specified number of lines.

        :param lines: the number of lines to feed
        :type lines: int, optional
        """

        if self.firmware_version >= 264:
            self.write_bytes(27, 100, lines)
            self.timeout_set(self.dot_feed_time * self.char_height)
            self.prev_byte = "\n"
            self.column = 0

        else:
            # datasheet claims sending bytes 27, 100, <x> works,
            # but it feeds much more than that.  So, manually:
            while lines > 0:
                self.write("\n".encode("cp437", "ignore"))
                lines -= 1

    def feed_rows(self, rows):
        """Feeds by the specified number of individual pixel rows."""

        self.write_bytes(27, 74, rows)
        self.timeout_set(rows * self.dot_feed_time)
        self.prev_byte = "\n"
        self.column = 0

    def flush(self) -> None:
        """Flush using ASCII FF."""

        self.write_bytes(12)

    def set_size(self, size: str) -> None:
        """Set the text size.

        S for small: single height, single width.
        M for medium: double height, single width.
        L for large: double width, double height.

        :param size: the size to use
        :type size: str
        :raises ValueError: if an invalid size is given
        """

        if size.upper() == "S":
            size = 0x00
            self.char_height = 24
            if self.alt_font is False:
                self.max_column = 32
            else:
                self.max_column = 42
        elif size.upper() == "M":
            size = 0x01
            self.char_height = 48
            if self.alt_font is False:
                self.max_column = 32
            else:
                self.max_column = 42
        elif size.upper() == "L":
            size = 0x11
            self.char_height = 48
            if self.alt_font is False:
                self.max_column = 16
            else:
                self.max_column = 21
        else:
            raise ValueError("Text size must be S, M, or L.")

        self.write_bytes(29, 33, size)

    def underline(self, weight: int) -> None:
        """Set the underline weight.

        0 for no underline.
        1 for thin underline.
        2 for thick underline.

        :param weight: the weight to use
        :type weight: int
        :raises ValueError: if an invalid weight is given
        """

        if weight not in (0, 1, 2):
            raise ValueError("Underline weight must be 0, 1, or 2.")
        self.write_bytes(27, 45, weight)

    def print_bitmap(self, width: int, height: int, bitmap: bytearray,
                     line_at_a_time: bool = False) -> None:
        """Print a bitmap.

        The max width is 384 pixels

        If line_at_a_time is True, print the image scanline-at-a-time
        (rather than in chunks). This tends to make for much cleaner
        printing (no feed gaps) on large images, but has the opposite
        effect on small images that would fit in a single 'chunk',
        so use carefully!

        :param width: the width in pixels
        :type width: int
        :param height: the height in pixels
        :type height: int
        :param bitmap: the bitmap to print as a list of (hex) numbers
        :type bitmap: bytearray
        :param line_at_a_time: whether to print scanline-at-a-time
        :type line_at_a_time: bool, optional
        """

        row_bytes = math.floor((width + 7) / 8)  # Round up to next byte boundary
        if row_bytes >= 48:
            row_bytes_clipped = 48  # 384 pixels max width
        else:
            row_bytes_clipped = row_bytes

        if line_at_a_time:
            max_chunk_height = 1
        else:
            max_chunk_height = 255

        i = 0
        for rowStart in range(0, height, max_chunk_height):
            chunk_height = height - rowStart
            if chunk_height > max_chunk_height:
                chunk_height = max_chunk_height

            # Timeout wait happens here
            self.write_bytes(18, 42, chunk_height, row_bytes_clipped)

            for y in range(chunk_height):
                for x in range(row_bytes_clipped):
                    super(AdafruitThermal,
                          self).write(bytes([bitmap[i]]))
                    i += 1
                i += row_bytes - row_bytes_clipped
            self.timeout_set(chunk_height * self.dot_print_time)

        self.prev_byte = "\n"

    def print_image(self, image_file: Union[str, pathlib.Path, BinaryIO],
                    line_at_a_time: bool = False) -> None:
        """Print an image.

        Image will be cropped to 384 pixels width if necessary, and
        converted to 1-bit w/diffusion dithering.
        Use the PIL to perform any other behaviour (e.g. scale,
        B&W threshold, etc) before passing the result to this function.

        If line_at_a_time is True, print the image scanline-at-a-time
        (rather than in chunks). This tends to make for much cleaner
        printing (no feed gaps) on large images, but has the opposite
        effect on small images that would fit in a single 'chunk',
        so use carefully!

        :param image_file: the image file to print
        :type image_file: Union[str, pathlib.Path, BinaryIO]
        :param line_at_a_time: whether to print scanline-at-a-time
        :type line_at_a_time: bool, optional
        """

        image = Image.open(image_file)
        if image.mode != "1":
            image = image.convert("1")

        width = image.size[0]
        height = image.size[1]
        if width > 384:
            width = 384
        row_bytes = math.floor((width + 7) / 8)
        bitmap = bytearray(row_bytes * height)
        pixels = image.load()

        for y in range(height):
            n = y * row_bytes
            x = 0
            for b in range(row_bytes):
                total = 0
                bit = 128
                while bit > 0:
                    if x >= width:
                        break
                    if pixels[x, y] == 0:
                        total |= bit
                    x += 1
                    bit >>= 1
                bitmap[n + b] = total

        self.print_bitmap(width, height, bitmap, line_at_a_time)

    def offline(self) -> None:
        """Take the printer offline.

        Print commands sent after this will be ignored until online() is called.
        """

        self.write_bytes(27, 61, 0)

    def online(self) -> None:
        """Take the printer online. Subsequent print commands will be obeyed."""
        self.write_bytes(27, 61, 1)

    def sleep(self, seconds: int = 1) -> None:
        """Put the printer into a low-energy state.

        :param seconds: how long to wait
        :type seconds: int, optional
        """

        if self.firmware_version >= 264:
            self.write_bytes(27, 56, seconds & 0xFF, seconds >> 8)
        else:
            self.write_bytes(27, 56, seconds)

    def wake(self) -> None:
        """Take the printer out of the low-energy state."""

        self.timeout_set(0)
        self.write_bytes(255)
        if self.firmware_version >= 264:
            time.sleep(0.05)  # 50 ms
            self.write_bytes(27, 118, 0)  # Sleep off (important!)
        else:
            for i in range(10):
                self.write_bytes(27)
                self.timeout_set(0.1)

    def has_paper(self) -> bool:
        """Check the status of the paper.

        This uses the printer's self-reporting ability.
        It doesn't match the datasheet

        :return: True if paper present, False for no paper
        """

        self.flush()
        if self.firmware_version >= 264:
            self.write_bytes(27, 118, 0)
        else:
            self.write_bytes(29, 114, 0)
        # Bit 2 of response seems to be paper status
        result = self.read(1)
        if len(result) > 0:
            stat = ord(result) & 0b00000100
            # If set, no paper; if clear, we have paper
            return stat != 0
        return True

    def set_line_height(self, val: int = 32) -> None:
        """Sets the line spacing.

        The printer doesn't take into account the current text height
        when setting line height, making this more akin to inter-line
        spacing.

        Default is 32 (char height of 24, line spacing of 8).

        :param val: the line spacing to set
        :type val: int
        """

        if val < 24:
            val = 24
        self.line_spacing = val - 24
        self.write_bytes(27, 51, val)

    def set_charset(self, charset: Charset = Charset.CHARSET_UK) -> None:
        """Set the charset.

        This alters some chars in ASCII 0x23-0x7E range, see datasheet.

        :param charset: the charset to use
        :type charset: Charset
        """

        self.write_bytes(27, 82, charset.value)

    def set_code_page(self,
                      codepage: Codepage = Codepage.CODEPAGE_CP437) -> None:
        """Selects alternative symbols for ASCII values 0x80-0xFF.

        :param codepage: the codepage to use
        :type codepage: Codepage
        """

        self.write_bytes(27, 116, codepage.value)

    def println(self, text: Any, wrap: bool = False, newline: bool = True) -> None:
        """Print the text.

        :param text: the text to print
        :type text: Any
        :param wrap: whether to wrap the text
        :type wrap: bool, optional
        :param newline: whether to write a newline at the end
        :type newline: bool, optional
        """

        if self.sideways is True:
            text = str(text)[::-1]
        elif wrap is True:
            text = textwrap.fill(str(text), self.max_column)
        self.write((str(text)).encode("cp437", "ignore"))
        if newline is True:
            self.write("\n".encode("cp437", "ignore"))
