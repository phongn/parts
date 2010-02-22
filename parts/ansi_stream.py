import ctypes
import color
import sys
win32=sys.platform == 'win32'

class ColorTextStream(object):
    '''Basically is an object that wraps a stream and process color ansi 
    command codes for color
    '''

    def __init__(self,stream,out_lock,col=color.ConsoleColor(),use_color=False):
        #the stream object
        self.stream=stream
        self.m_lock=out_lock
        # default colors for this stream 
        self.color=col
        self.reset=color.ConsoleColor(color.SystemColor)
        if col.Background() == color.Default and col.Foreground() == color.Default:
            self.ProcessColor=False
        else:
            self.ProcessColor =use_color
    
    def write(self,s):
        self.m_lock.acquire()
        try:
            if self.ProcessColor :            
                self._WriteColor(self.color.ansi_value()+s+self.reset.ansi_value())
            else:
                self._WriteNoColor(s)
        finally:
            self.m_lock.release()
        
    
    def writeLines(self,str_list):
        
        self.m_lock.acquire()
        try:
            if self.ProcessColor :
                self._WriteColor(self.color.ansi_value())
                for s in str_list:
                    self._WriteNoColor(s)
                self._WriteColor(self.reset.ansi_value())
            else:
                for s in str_list:
                    self._WriteNoColor(s)
        finally:
            self.m_lock.release()
        
    if win32:
        def SetColor(self,console_color):
            handle = ctypes.windll.kernel32.GetStdHandle(-11)
            bool = ctypes.windll.kernel32.SetConsoleTextAttribute(handle, console_color.SystemValue())
    
    def _WriteColor(self,in_str):
        #self.stream.write(in_str)
        if win32:
            tmp_str=''
            state=0
            code=0
            col=color.ConsoleColor(color.default_color.Foreground(),color.default_color.Background())
            fg_int=0
            bk_int=0
            fg_bold=None
            bk_bold=None
            for s in in_str:
                if s == '\033':
                    state=1
                    if tmp_str!='':
                        self.stream.write(tmp_str)
                        tmp_str=''
                elif s == '[' and state==1:
                    state=2
                elif state==2:
                    if s == ';' or s=='m':
                        #process code
                        if code >=30  and code < 38:
                            col.Foreground(code-30)
                        elif code >=90  and code < 98:
                            col.Foreground(code-82)
                            fg_bold=True
                        elif code >=40  and code < 48:
                            col.Background(code-40)
                        elif code >=100  and code < 108:
                            col.Background(code-92)
                            bk_bold=True
                        elif code == 1:
                            fg_bold=True
                        elif code == 2:
                            fg_bold=False
                            
                        elif code==0:
                            #reset
                            col.Background(color.default_color.Background())
                            col.Foreground(color.default_color.Foreground())
                            fg_bold=None
                            bk_bold=None
                        code=0
                    else:
                        try:            
                            code=code*10+int(s)
                        except ValueError:
                            
                            code=0
                            state=0
                    if s=='m':
                        if fg_bold == True:
                            tmp=col.Foreground()
                            if tmp < 8:
                                col.Foreground(tmp+8)
                        elif fg_bold == False:
                            tmp=col.Foreground()
                            if tmp > 7 :
                                col.Foreground(tmp-8)
                        if bk_bold == True:
                            tmp=col.Background()
                            if tmp < 8:
                                col.Background(tmp+8)
                        self.SetColor(col)
                        state=0
                        code=0
                else:           
                    tmp_str+=s
            if tmp_str != '':
                self.stream.write(tmp_str)
        else:
            self.stream.write(in_str)
            
    def _WriteNoColor(self,in_str):
        '''Will just strip the codes'''
        
        tmp_str=''
        state=0
        code=0
        for s in in_str:
            if s == '\033':
                state=1
                self.stream.write(tmp_str)
                tmp_str=''
            elif s == '[' and state==1:
                state=2
            elif state==2:
                if s == ';' or s=='m':
                    code=0
                else:
                    try:            
                        code=code*10+int(s)
                    except ValueError:
                        
                        code=0
                        state=0
                if s=='m':
                    
                    state=0
                    code=0
            else:           
                tmp_str+=s
        if tmp_str != '':
            self.stream.write(tmp_str)
