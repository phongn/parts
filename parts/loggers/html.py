# simple HTML logger


import SCons.Script
import parts.logger as logger
import parts.color as color
import os
import sys


# html Simple logger. Probally needs more work.


def RtfColorIndex (col): 
    if col == color.Black: ret = "black"
    elif col==color.Blue:  ret = "blue" 
    elif col==color.Green: ret = "green"
    elif col==color.Cyan: ret = "aqua" 
    elif col==color.Red: ret = "red"  
    elif col==color.Magenta: ret = "purple" 
    elif col==color.Yellow: ret = "yellow" 
    elif col==color.White: ret = "white" 
    elif col==color.Gray: ret = "gray" 
    elif col==color.BrightBlue: ret = "brightblue" 
    elif col==color.BrightGreen: ret = "brightgreen" 
    elif col==color.BrightCyan: ret = "brightaqua"
    elif col==color.BrightRed: ret = "brightred" 
    elif col==color.BrightMagenta: ret = "brightmagenta" 
    elif col==color.BrightYellow: ret = "brightyellow" 
    elif col==color.BrightWhite: ret = "brightwhite" 
    else: ret = "black" 

    return ret
 



class html(logger.Logger):
    
    def __init__(self,dir,file):
        if os.path.exists(dir) == False:
            os.makedirs(dir)
        if file.endswith(".html") ==False:
            file+=".html"
        self.m_file=open(os.path.join(dir,file),"w")
        
        self.colors=SCons.Script.GetOption('use_color')
        self.fg_color=0
        self.writeheader()
        
    def writeheader(self):
        self.m_file.write('''<html>
<head>
    <title></title>
    <style type="text/css">
        .black
        {
            color: #000000;
        }
        .red
        {
            color: #800000;
        }
        .blue
        {
            color: #000080;
        }
        .green
        {
            color: #008000;
        }
        .yellow
        {
            color: #808000;
        }
        .aqua
        {
            color: #008080;
        }
        .purple
        {
            color: #800080;
        }
        .white
        {
            color: #808080;
        }
        .grey
        {
            color: #C0C0C0;
        }
        .brightred
        {
            color: #FF0000;
        }
        .brightblue
        {
            color: #0000FF;
        }
        .brightgreen
        {
            color: #00FF00;
        }
        .brightyellow
        {
            color: #FFFF00;
        }
        .brightaqua
        {
            color: #00FFFF;
        }
        .brightpurple
        {
            color: #FF00FF;
        }
        .brightwhite
        {
            color: #FFFFFF;
        }
    </style>
</head>
<body>
        ''')

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
        
        self.m_file.write("<span class=\"%s\">"%(RtfColorIndex(self.fg_color)))
        
    def writestr(self,msg):
        for c in msg:
            if c == '>':
                self.m_file.write('&gt')
            elif c == '<':
                self.m_file.write('&lt')
            elif c == '&':
                self.m_file.write('&amp')
            elif c == '\n':
                self.m_file.write('<br/>')
            else:
                self.m_file.write(c)
        self.m_file.write("</span>\n")
    
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
        self.m_file.write("</body></html>")
        self.m_file.close()