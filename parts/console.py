import ansi_stream
import color
import sys
import thread
 
import struct
import ctypes
# for non windows
if not color.is_win32:
    import fcntl
    import termios

class NullStream(object):

    def __init__(self):
        pass
    
    def write(self,s):
        pass
        
    def writeLines(self,str_list):
        pass
    
    def flush(self):
        pass

class Console:
    ''' only support output operations at this time'''
    out_stream=1
    error_stream=2
    warning_stream=3
    message_stream=4
    trace_stream=5
    verbose_stream=6
    def __init__(self,process_color=False):
        self.clearline=False
        self.__lock=thread.allocate_lock() # used to sync output cases across streams
        
        if color.is_win32:
            try:
                self.conio=open('con:','w')        
            except Exception,ec:
                self.conio= NullStream()               
        else:
            try: 
                self.conio=open('/dev/tty','w')
                
            except Exception,ec:
                self.conio=NullStream()        
        
        if color.is_win32==True:
            if color.default_color==color.ConsoleColor(0,0):
                process_color=False
                
        if process_color ==False:
            self.__console=ansi_stream.ColorTextStream(
                                        self,
                                        self.conio,
                                        use_color=True,
                                        flush=True,
                                        do_clearline=False
                                    )          
            self.Output=ansi_stream.ColorTextStream(
                                        self,            
                                        sys.__stdout__,
                                        use_color=False
                                    )
            self.Error=ansi_stream.ColorTextStream(
                                        self,
                                        sys.__stderr__,
                                        use_color=False
                                    )
            self.Warning=ansi_stream.ColorTextStream(
                                        self,
                                        sys.__stderr__,
                                        use_color=False
                                    )
            self.Message=ansi_stream.ColorTextStream(
                                        self,
                                        sys.__stdout__,
                                        use_color=False
                                    )
            self.Trace=ansi_stream.ColorTextStream(
                                        self,
                                        sys.__stdout__,
                                        use_color=False
                                    )
            self.Verbose=ansi_stream.ColorTextStream(
                                        self,
                                        sys.__stdout__,
                                        use_color=False
                                    )
            
        else:
            self.__console=ansi_stream.ColorTextStream(
                                        self,
                                        self.conio,
                                        color.ConsoleColor(color.BrightMagenta),
                                        use_color=True,
                                        flush=True,
                                        do_clearline=False
                                    )                
            self.Output=ansi_stream.ColorTextStream(
                                        self,
                                        sys.__stdout__,
                                        process_color['stdout'],
                                        use_color=True
                                    )
            self.Error=ansi_stream.ColorTextStream(
                                        self,
                                        sys.__stdout__,
                                        process_color['stderr'],
                                        use_color=True
                                    )
            self.Warning=ansi_stream.ColorTextStream(
                                        self,
                                        sys.__stdout__,
                                        process_color['stdwrn'],
                                        use_color=True
                                    )
            self.Message=ansi_stream.ColorTextStream(
                                        self,
                                        sys.__stdout__,
                                        process_color['stdmsg'],
                                        use_color=True
                                    )
            self.Trace=ansi_stream.ColorTextStream(
                                        self,
                                        sys.__stdout__,
                                        process_color['stdtrace'],
                                        use_color=True
                                    )
            self.Verbose=ansi_stream.ColorTextStream(
                                        self,
                                        sys.__stdout__,
                                        process_color['stdverbose'],
                                        use_color=True
                                    )
    
    def ShutDown(self):
        sys.stdout=sys.__stdout__
        sys.stdout=sys.__stderr__
        

        
    def write(self,msg):
        ## write data
        self.__console.write(msg)
        self.clearline=True
        
    def flush(self):
        ## write data
        self.__console.flush()
        
    if color.is_win32:
        @property
        def Width(self):
            # move to common var prevent repeating the getting of common value
            handle = ctypes.windll.kernel32.GetStdHandle(-12)        
            string_buffer = ctypes.create_string_buffer(22)        
            ret = ctypes.windll.kernel32.GetConsoleScreenBufferInfo(handle, string_buffer)            
            wattr=0
            if ret:
                (bufx, bufy, curx, cury, wattr,left, top, right, bottom, maxx, maxy) = struct.unpack("hhhhHhhhhhh", string_buffer.raw)
                return  right - left + 1
            return 80
        
        @property
        def Height(self):
            # move to common var prevent repeating the getting of common value
            handle = ctypes.windll.kernel32.GetStdHandle(-12)        
            string_buffer = ctypes.create_string_buffer(22)        
            ret = ctypes.windll.kernel32.GetConsoleScreenBufferInfo(handle, string_buffer)            
            wattr=0
            if ret:
                (bufx, bufy, curx, cury, wattr,left, top, right, bottom, maxx, maxy) = struct.unpack("hhhhHhhhhhh", string_buffer.raw)
                return  bottom - top + 1
            return 40
    else:
        @property
        def Width(self):
            width = 0
            try:
                tmp = struct.pack('HHHH', 0, 0, 0, 0)
                data = fcntl.ioctl(1, termios.TIOCGWINSZ, tmp)
                width = struct.unpack('HHHH', data)[1]
            except IOError:
                pass     
            # something went wrong
            if width <= 0:
                width = 80

            return width
        
        @property
        def Height(self):
            height = 0
            try:
                tmp = struct.pack('HHHH', 0, 0, 0, 0)
                data = fcntl.ioctl(1, termios.TIOCGWINSZ, tmp)
                height = struct.unpack('HHHH', data)[0]
            except IOError:
                pass     
            # something went wrong
            if height <= 0:
                height = 40

            return height
    
        
    def ClearLine(self):
        s="\r"+(" "*(self.Width-1))+"\r"
        self.__console.write(s,lock=not self.__lock.locked)
        
    def lock(self):
        self.__lock.acquire()
        
    def release(self):
        self.__lock.release()


