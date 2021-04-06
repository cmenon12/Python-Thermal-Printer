from enum import Enum


class Barcode(Enum):
    UPC_A = 0
    UPC_E = 1
    EAN13 = 2
    EAN8 = 3
    CODE39 = 4
    I25 = 5
    CODEBAR = 6
    CODE93 = 7
    CODE128 = 8
    CODE11 = 9
    MSI = 10
    ITF = 11
    CODABAR = 12


class Charset(Enum):
    CHARSET_USA = 0
    CHARSET_FRANCE = 1
    CHARSET_GERMANY = 2
    CHARSET_UK = 3
    CHARSET_DENMARK1 = 4
    CHARSET_SWEDEN = 5
    CHARSET_ITALY = 6
    CHARSET_SPAIN1 = 7
    CHARSET_JAPAN = 8
    CHARSET_NORWAY = 9
    CHARSET_DENMARK2 = 10
    CHARSET_SPAIN2 = 11
    CHARSET_LATINAMERICA = 12
    CHARSET_KOREA = 13
    CHARSET_SLOVENIA = 14
    CHARSET_CROATIA = 14
    CHARSET_CHINA = 15


class Codepage(Enum):
    CODEPAGE_CP437 = 0  # USA, Standard Europe
    CODEPAGE_KATAKANA = 1
    CODEPAGE_CP850 = 2  # Multilingual
    CODEPAGE_CP860 = 3  # Portuguese
    CODEPAGE_CP863 = 4  # Canadian-French
    CODEPAGE_CP865 = 5  # Nordic
    CODEPAGE_WCP1251 = 6  # Cyrillic
    CODEPAGE_CP866 = 7  # Cyrillic #2
    CODEPAGE_MIK = 8  # Cyrillic/Bulgarian
    CODEPAGE_CP755 = 9  # East Europe, Latvian 2
    CODEPAGE_IRAN = 10
    CODEPAGE_CP862 = 15  # Hebrew
    CODEPAGE_WCP1252 = 16  # Latin 1
    CODEPAGE_WCP1253 = 17  # Greek
    CODEPAGE_CP852 = 18  # Latin 2
    CODEPAGE_CP858 = 19  # Multilingual Latin 1 + Euro
    CODEPAGE_IRAN2 = 20
    CODEPAGE_LATVIAN = 21
    CODEPAGE_CP864 = 22  # Arabic
    CODEPAGE_ISO_8859_1 = 23  # West Europe
    CODEPAGE_CP737 = 24  # Greek
    CODEPAGE_WCP1257 = 25  # Baltic
    CODEPAGE_THAI = 26
    CODEPAGE_CP720 = 27  # Arabic
    CODEPAGE_CP855 = 28
    CODEPAGE_CP857 = 29  # Turkish
    CODEPAGE_WCP1250 = 30  # Central Europe
    CODEPAGE_CP775 = 31
    CODEPAGE_WCP1254 = 32  # Turkish
    CODEPAGE_WCP1255 = 33  # Hebrew
    CODEPAGE_WCP1256 = 34  # Arabic
    CODEPAGE_WCP1258 = 35  # Vietnam
    CODEPAGE_ISO_8859_2 = 36  # Latin 2
    CODEPAGE_ISO_8859_3 = 37  # Latin 3
    CODEPAGE_ISO_8859_4 = 38  # Baltic
    CODEPAGE_ISO_8859_5 = 39  # Cyrillic
    CODEPAGE_ISO_8859_6 = 40  # Arabic
    CODEPAGE_ISO_8859_7 = 41  # Greek
    CODEPAGE_ISO_8859_8 = 42  # Hebrew
    CODEPAGE_ISO_8859_9 = 43  # Turkish
    CODEPAGE_ISO_8859_15 = 44  # Latin 3
    CODEPAGE_THAI2 = 45
    CODEPAGE_CP856 = 46
    CODEPAGE_CP874 = 47


class PrintMode(Enum):
    SMALL_FONT_MASK = (1 << 1)
    UPDOWN_MASK = (1 << 2)
    BOLD_MASK = (1 << 3)
    DOUBLE_HEIGHT_MASK = (1 << 4)
    DOUBLE_WIDTH_MASK = (1 << 5)
    STRIKE_MASK = (1 << 6)
