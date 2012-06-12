
import SCons.Script
import parts.logger as logger
import parts.color as color
import os
import sys


# rtf Simple logger. Probally needs more work.


def RtfColorIndex (col): 
    if col == color.Black: ret = 17
    elif col==color.Blue:  ret = 2 
    elif col==color.Green: ret = 3
    elif col==color.Cyan: ret = 4 
    elif col==color.Red: ret = 5  
    elif col==color.Magenta: ret = 6 
    elif col==color.Yellow: ret = 7 
    elif col==color.White: ret = 8 
    elif col==color.Gray: ret = 9 
    elif col==color.BrightBlue: ret = 10 
    elif col==color.BrightGreen: ret = 11 
    elif col==color.BrightCyan: ret = 12 
    elif col==color.BrightRed: ret = 13 
    elif col==color.BrightMagenta: ret = 14 
    elif col==color.BrightYellow: ret = 15 
    elif col==color.BrightWhite: ret = 16 
    else: ret = 0 

    return ret
 



class rtf(logger.Logger):
    
    def __init__(self,dir,file):
        if os.path.exists(dir) == False:
            os.makedirs(dir)
        if file.endswith(".rtf") ==False:
            file+=".rtf"
        self.m_file=open(os.path.join(dir,file),"w")
        
        self.colors=SCons.Script.GetOption('use_color')
        self.fg_color=0
        self.writeheader()
        super(rtf, self).__init__(dir,file)
        
    def writeheader(self):
        self.m_file.write("{\\rtf1\\fbidis\\ansi\\ansicpg1252")
        self.m_file.write('''{\\colortbl;red0\\green0\\blue128;\\red0\\green128\\blue0;\\red0\\green128\\blue128;\
\\red128\\green0\\blue0;\\red1\\green36\\blue86;\\red238\\green237\\blue240;\\red192\\green192\\blue192;\
\\red128\\green128\\blue128;\\red0\\green0\\blue255;\\red0\\green255\\blue0;\\red0\\green255\\blue255;\
\\red255\\green0\\blue0;\\red255\\green0\\blue255;\\red255\\green255\\blue0;\\red255\\green255\\blue255;\\red0\\green0\\blue0;}\n''')
        self.m_file.write('\\viewkind4\\pard')

    def out_color(self,col):
        fg=col.Foreground()
        if fg == color.Bright:
            if self.fg_color < 8:
                fg=self.fg_color+8
            else:
                fg=self.fg_color
        elif fg == color.Dim:
            if self.fg_color > 8:
                fg=self.fg_color-8
            else:
                fg=self.fg_color
        else:
            self.fg_color=fg
        
        self.m_file.write("\\cf1\\cf%s "%(RtfColorIndex(self.fg_color)))
        
    def writestr(self,msg):
        for c in msg:
            if c == '\t':
                self.m_file.write('\\tab')
            elif c == '\\':
                self.m_file.write('\\\\')
            elif c == '{':
                self.m_file.write('\\{')
            elif c == '}':
                self.m_file.write('\\}')
            elif c == '\n':
                self.m_file.write('\\par\n')
            else:
                self.m_file.write(c)
    
    def logout(self,msg):
        self.out_color(self.colors['stdout'])
        self.writestr(msg)
        
    def logerr(self,msg):
        self.out_color(self.colors['stderr'])
        self.writestr(msg)
        
    def logwrn(self,msg):
        self.out_color(self.colors['stdwrn'])
        self.writestr(msg)
    
    def logmsg(self,msg):
        self.out_color(self.colors['stdmsg'])
        self.writestr(msg)

    def logtrace(self,msg):
        self.out_color(self.colors['stdtrace'])
        self.writestr(msg)
    
    def logverbose(self,msg):
        self.out_color(self.colors['stdverbose'])
        self.writestr(msg)
    
    def shutdown(self):
        self.m_file.write("}")
        self.m_file.close()