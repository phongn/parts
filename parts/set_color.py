# See http://msdn.microsoft.com/library/default.asp?url=/library/en-us/winprog/winprog/windows_api_reference.asp
# for information on Windows APIs.
import common
import ctypes
import sys


class win32_set_color:     
    BLACK = 0x00
    DARK_BLUE = 0x01
    DARK_GREEN = 0x02
    DARK_AQUA = 0x03
    DARK_RED  = 0x04 
    DARK_PURPLE = 0x05
    DARK_YELLOW = 0x06
    DARK_WHITE = 0x07
    GRAY = 0x08
    BLUE = 0x09
    GREEN = 0x0A
    AQUA = 0x0B
    RED = 0x0C
    PURPLE = 0x0D
    YELLOW = 0x0E
    BRIGHT_WHITE = 0x0F

    BG_BLACK = 0x00
    BG_DARK_BLUE = 0x10
    BG_DARK_GREEN = 0x20 
    BG_DARK_AQUA = 0x30
    BG_DARK_RED  = 0x40
    BG_DARK_PURPLE = 0x50
    BG_DARK_YELLOW = 0x60
    BG_DARK_WHITE = 0x70
    BG_GRAY = 0x80
    BG_BLUE = 0x90
    BG_GREEN = 0xA0
    BG_AQUA = 0xB0
    BG_RED = 0xC0
    BG_PURPLE = 0xD0
    BG_YELLOW = 0xE0
    BG_WHITE = 0xF0

    STD_INPUT_HANDLE = -10
    STD_OUTPUT_HANDLE= -11
    STD_ERROR_HANDLE = -12
    
    def __init__(self):
        self.orig_color = self.get_color()        
        
    def set_color(self,color,msg):
        """    
        Example: set_color(GREEN)
        """
        handle = ctypes.windll.kernel32.GetStdHandle(win32_set_color.STD_OUTPUT_HANDLE)
        bool = ctypes.windll.kernel32.SetConsoleTextAttribute(handle, color)
        return msg
        
    def get_color(self):
        handle = ctypes.windll.kernel32.GetStdHandle(win32_set_color.STD_OUTPUT_HANDLE)        
        string_buffer = ctypes.create_string_buffer(22)        
        bool = ctypes.windll.kernel32.GetConsoleScreenBufferInfo(handle, string_buffer)
        wattr=0
        if bool:
            import struct
            (bufx, bufy, curx, cury, wattr,left, top, right, bottom, maxx, maxy) = struct.unpack("hhhhHhhhhhh", string_buffer.raw)
        
        if wattr > 0:
            return wattr

# Work in Progress         
class posix_set_color:
    BLACK = "\x1b[30;06m"
    DARK_BLUE = "\x1b[34;06m"
    DARK_GREEN = "\x1b[32;06m"
    DARK_AQUA = "\x1b[36;06m"
    DARK_RED  = "\x1b[31;06m"
    DARK_PURPLE = "\x1b[35;06m"
    DARK_YELLOW = "\x1b[33;06m"
    GRAY = "\x1b[37;06m"
    BLUE = "\x1b[34;01m"
    GREEN = "\x1b[32;01m"
    AQUA = "\x1b[36;01m"
    RED = "\x1b[31;01m"
    PURPLE = "\x1b[35;01m"
    YELLOW = "\x1b[33;01m"
    BRIGHT_WHITE = "\x1b[37;01m"
    RESET = "\x1b[0m"

    BG_BLACK = 0x00
    BG_DARK_BLUE = 0x10
    BG_DARK_GREEN = 0x20 
    BG_DARK_AQUA = 0x30
    BG_DARK_RED  = 0x40
    BG_DARK_PURPLE = 0x50
    BG_DARK_YELLOW = 0x60
    BG_DARK_WHITE = 0x70
    BG_GRAY = 0x80
    BG_BLUE = 0x90
    BG_GREEN = 0xA0
    BG_AQUA = 0xB0
    BG_RED = 0xC0
    BG_PURPLE = 0xD0
    BG_YELLOW = 0xE0
    BG_WHITE = 0xF0
    def __init__(self):
        self.orig_color = posix_set_color.RESET        
        
    def set_color(self,color,msg):
        """    
        Example: set_color(GREEN)
        """   
        msg = color + msg + self.orig_color
        return msg
        
    def get_color(self):
        handle = ctypes.windll.kernel32.GetStdHandle(win32_set_color.STD_OUTPUT_HANDLE)        
        string_buffer = ctypes.create_string_buffer(22)        
        bool = ctypes.windll.kernel32.GetConsoleScreenBufferInfo(handle, string_buffer)
        wattr=0
        if bool:
            import struct
            (bufx, bufy, curx, cury, wattr,left, top, right, bottom, maxx, maxy) = struct.unpack("hhhhHhhhhhh", string_buffer.raw)
        if wattr > 0:
            return wattr
    

    pass

    
if sys.platform=='win32' :
    base=win32_set_color
else:
    base=posix_set_color

class colors(base):
    pass    