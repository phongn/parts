import ansi_stream
import color
import sys
import thread

class Console:
    ''' only support output operations at this time'''
    out_stream=1
    error_stream=2
    warning_stream=3
    message_stream=4
    trace_stream=5
    verbose_stream=6
    def __init__(self,process_color=False):

        self.m_lock=thread.allocate_lock() # used to sync output cases across streams
        
        if color.is_win32==True:
            if color.default_color==color.ConsoleColor(0,0):
                process_color=None
        if process_color is None:
            #self.__console=ansi_stream.ColorTextStream(conio,use_color=process_color)                
            self.Output=ansi_stream.ColorTextStream(
                                        sys.__stdout__,
                                        self.m_lock,
                                        use_color=False
                                    )
            self.Error=ansi_stream.ColorTextStream(
                                        sys.__stderr__,
                                        self.m_lock,
                                        use_color=False
                                    )
            self.Warning=ansi_stream.ColorTextStream(
                                        sys.__stderr__,
                                        self.m_lock,
                                        use_color=False
                                    )
            self.Message=ansi_stream.ColorTextStream(
                                        sys.__stdout__,
                                        self.m_lock,
                                        use_color=False
                                    )
            self.Trace=ansi_stream.ColorTextStream(
                                        sys.__stdout__,
                                        self.m_lock,
                                        use_color=False
                                    )
            self.Verbose=ansi_stream.ColorTextStream(
                                        sys.__stdout__,
                                        self.m_lock,
                                        use_color=False
                                    )
            
        else:
            #self.__console=ansi_stream.ColorTextStream(conio,color.Purple,use_color=process_color)                
            self.Output=ansi_stream.ColorTextStream(
                                        sys.__stdout__,
                                        self.m_lock,
                                        process_color['stdout'],
                                        use_color=True
                                    )
            self.Error=ansi_stream.ColorTextStream(
                                        sys.__stdout__,
                                        self.m_lock,
                                        process_color['stderr'],
                                        use_color=True
                                    )
            self.Warning=ansi_stream.ColorTextStream(
                                        sys.__stdout__,
                                        self.m_lock,
                                        process_color['stdwrn'],
                                        use_color=True
                                    )
            self.Message=ansi_stream.ColorTextStream(
                                        sys.__stdout__,
                                        self.m_lock,
                                        process_color['stdmsg'],
                                        use_color=True
                                    )
            self.Trace=ansi_stream.ColorTextStream(
                                        sys.__stdout__,
                                        self.m_lock,
                                        process_color['stdtrace'],
                                        use_color=True
                                    )
            self.Verbose=ansi_stream.ColorTextStream(
                                        sys.__stdout__,
                                        self.m_lock,
                                        process_color['stdverbose'],
                                        use_color=True
                                    )
    
    def ShutDown(self):
        sys.stdout=sys.__stdout__
        sys.stdout=sys.__stderr__
        

        
    def Write(self,msg):
        ## write data
        print msg
        pass#self.__console.Write(msg)
    



