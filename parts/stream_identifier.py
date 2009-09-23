import common
import string
import re

class Stream_Identifier:
    NONE = 0
    OUTPUT = 1
    ERROR = 2
    WARNING = 3
    def __init__(self):
        self.identity = Stream_Identifier.NONE
        self.warning = re.compile('((\s|\W)warnings?(\W\s|\s))|(warnings?\s?:)',re.IGNORECASE)
        self.error = re.compile('((\s|\W)errors?(\W\s|\s))|(errors?\s?:)',re.IGNORECASE)
        
    def stream_identify(self,line,default = OUTPUT):
        self.identity = Stream_Identifier.NONE
        if self.warning.search(line):
            self.identity = Stream_Identifier.WARNING
        if self.error.search(line):
            self.identity = Stream_Identifier.ERROR
        if self.identity is Stream_Identifier.NONE:
            self.identity = default
