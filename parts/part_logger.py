import common
import console
import SCons.Script
import subprocess,sys,string,os
import thread,threading 


##is_windows = (sys.platform == "win32")
##
##if is_windows:
##    import win32event,win32process, win32pipe, win32con, win32api,win32file
##    def win32_spawn(args,
##                shell,
##                executable,
##                env):
##        
##
##        startInfo = win32process.STARTUPINFO() 
##        startInfo.dwFlags = win32process.STARTF_USESTDHANDLES
##        startInfo.dwFlags |= win32process.STARTF_USESHOWWINDOW
##        startInfo.wShowWindow = win32con.SW_HIDE
##
##        outread, outwrite = win32pipe.CreatePipe(None, 0)
##        errread, errwrite = win32pipe.CreatePipe(None, 0)
##        
##        outwrite2=win32api.DuplicateHandle(win32api.GetCurrentProcess(), outwrite,
##                                   win32api.GetCurrentProcess(), 0, 1,
##                                   win32con.DUPLICATE_SAME_ACCESS)
##        errwrite2=win32api.DuplicateHandle(win32api.GetCurrentProcess(), errwrite,
##                                   win32api.GetCurrentProcess(), 0, 1,
##                                   win32con.DUPLICATE_SAME_ACCESS)
##
##        startInfo.hStdInput = win32api.GetStdHandle(win32api.STD_INPUT_HANDLE)
##        startInfo.hStdOutput = outwrite2
##        startInfo.hStdError = errwrite2    
##        args = "cmd.exe" + " /c " + args
##        hp, ht, pid, tid = win32process.CreateProcess(executable, args,
##                                             None, None,
##                                             1,
##                                             0,
##                                             env,
##                                             None,
##                                             startInfo)
##
##        ht.Close()
##        outwrite2.Close()
##        errwrite2.Close()
##
##        return (hp,outread,errread)
##
##    def func(id,out,output):
##        #id,out,output=args
##        try:  
##            
##            while True:
##                r,s=win32file.ReadFile(out,1024)
##                output.WriteOut(id,s)
##
##        except:
##            pass
##    
##
##class part_spawner:
##    def __init__(self,env):
##        self.env=env   
##
##    def __call__(self,shell, escape, cmd, args, Env):
##        # setup the call        
##        
##        ENV={}
##        for k,v in Env.iteritems():
##            ENV[k]=str(v)
##        # get the part_logger
##        output=self.env["PART_LOG_MAPPER"]
##        
##        
##        #it seems that the escape work for windows  (but does not seem needed)
##        # however the escape function really messes up Linux
##        if self.env["PLATFORM"]=="win32":
##            command_line = escape(string.join(args))
##        else:
##            command_line = string.join(args)
##        
##        #tell it we are starting a given action/command, get action_id
##        id=output.TaskStart(command_line)   
##        
##        
##        # get the output and redirect to logger
##        if is_windows:
##            proc,out,err = win32_spawn(command_line,
##                shell=True,
##                executable=shell,
##                env=ENV)
##            win32process.beginthreadex(None, 0, func , (id,out,output) , 0)
##            win32process.beginthreadex(None, 0, func , (id,err,output) , 0)
##
##            win32event.WaitForSingleObject(proc,win32event.INFINITE)
##            ret = win32process.GetExitCodeProcess(proc)
##
##        else:
##            import select
##            # do the call
##            proc = subprocess.Popen(
##                command_line,
##                shell=True,
##                executable=shell,
##                env=ENV,
##                stdout=subprocess.PIPE,
##                stderr=subprocess.PIPE)
##            
##            while (proc.poll () == None):
##                il,ol,el=select.select([proc.stdout,proc.stderr],[],[])
##                for i in il:
##                    if i == proc.stdout:
##                        output.WriteOut(id,proc.stdout.readline ())
##                    elif i == proc.stderr:
##                        output.WriteErr(id,proc.stderr.readline ())
##                
##            output.WriteOut(id,proc.stdout.read ())
##            output.WriteErr(id,proc.stderr.read ())
##        
##        # we are done tell logger this action is done.
##            ret = proc.returncode
##        output.TaskEnd(id,ret)
##        return ret
##    
class pipeRedirector:
    def _readerthread(self):
        l = ' '
        while l != '':
            l = self.pipein.readline()
            if l != "":
                self.writer(l)

    def __init__(self,pipein,writer):
        self.pipein = pipein
        self.writer = writer
        self.thread = threading.Thread(target=self._readerthread,
                args=())
        self.executing = True
        self.thread.start()

    def close(self):
        self.executing = False
        self.thread.join()
        self.pipein = None
        self.thread = None
        self.writer = None

class part_spawner:
    def __init__(self,env):
        self.env=env   

    def __call__(self,shell, escape, cmd, args, Env):
        # setup the call        
        
        ENV={}
        for k,v in Env.iteritems():
            ENV[k]=str(v)
        # get the part_logger
        output=self.env["PART_LOG_MAPPER"]
        #tell it we are starting a given actio/command, get action_id
        
        #it seems that the escape work for windows  (but does not seem needed)
        # however the escape function really messes up Linux
        if self.env["PLATFORM"]=="win32":
            command_line = escape(string.join(args))
        else:
            command_line = string.join(args)
        
        id=output.TaskStart(command_line)   
        
        # do the call
        proc = subprocess.Popen(
            command_line,
            shell=True,
            executable=shell,
            env=ENV,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)#,
            #universal_newlines=True)

        # get the output and redirect to logger
        p1 = pipeRedirector(proc.stdout, lambda x: output.WriteOut(id, x))
        p2 = pipeRedirector(proc.stderr, lambda x: output.WriteErr(id, x))
        
        try:
            proc.wait()
        except OSError, e:
            if e.errno != 10:
                raise e


        # force pipe-redirectors to close handles
        p1.close()
        p2.close()
        
        # we are done tell logger this action is done.
        ret = proc.returncode
        output.TaskEnd(id,ret)
        return ret



class part_logger:
    def __init__(self,env,console):
        self.env=env
        def_env=SCons.Script.DefaultEnvironment()
        self.reporter=def_env['PARTS_REPORTER']
        self.block_text=2#SCons.Script.GetOption('num_jobs') > 1
        self.cache={}

        log=env['PART_LOGGER']
        if common.is_string(log):
            if log[0]!='$':
                log="$"+log
            log = env.subst(log, raw=1, conv=lambda x: x)
            if common.is_string(log):
                log=part_nil_logger
        self.other_out=log()

    def TaskStart(self,msg):
        id=hash(msg)
        self.cache[id]=[]
        self.other_out.Start(self.env,id,msg)
        return id
    
    def TaskEnd(self,id,exit_code):

        self._empty_cache(id) 
        self.other_out.End(self.env,id,exit_code)
        del self.cache[id]

    def WriteOut(self,id,msg):
        if self.block_text==False:
            self.reporter.stdout(msg)
            self.other_out.Out(self.env,id,msg)
        else:
            try:
                tmp=self.cache[id][-1][0]
            except IndexError:
                tmp=None
            if tmp == console.Console.out_stream:
               self.cache[id][-1][1] += msg
            elif self.block_text == 2: # simple chaching
                self._empty_cache(id) # this different so flush it
                self.cache[id].append([console.Console.out_stream,msg])
            else:
                self.cache[id].append([console.Console.out_stream,msg])
        
        
    def WriteErr(self,id,msg):
        
        if self.block_text==False:
            self.reporter.stderr(msg)
            self.other_out.Err(self.env,id,msg)
        else:
            try:
                tmp=self.cache[id][-1][0]
            except IndexError:
                tmp=None
            if tmp == console.Console.error_stream:
               self.cache[id][-1][1] += msg
            elif self.block_text == 2: # simple chaching
                self._empty_cache(id) # this different so flush it
                self.cache[id].append([console.Console.error_stream,msg])
            else: #full caching
                self.cache[id].append([console.Console.error_stream,msg])
    
    def _empty_cache(self,id):
        for text in self.cache[id]:
            if text[0] == console.Console.out_stream:
                brkup=text[1].split('\n')
                grpstr=''
                for s in brkup:
                    if s == '':
                        pass
                    elif grpstr == '':
                        grpstr=s+'\n'
                    elif s[0]==' ' or s[0]=='\t': # group indented text
                        grpstr+=s+'\n'
                    else:
                        self.reporter.stdout(grpstr)
                        self.other_out.Out(self.env,id,grpstr)
                        grpstr=s+'\n'
                else:
                    self.reporter.stdout(grpstr)
                    self.other_out.Out(self.env,id,grpstr)
            elif text[0] ==console.Console.error_stream:
                brkup=text[1].split('\n')
                grpstr=''
                for s in brkup:
                    if s == '':
                        pass
                    elif grpstr == '':
                        grpstr=s+'\n'
                    elif s[0]==' ' or s[0]=='\t': # group indented text
                        grpstr+=s+'\n'
                    else:
                        self.reporter.stderr(grpstr)
                        self.other_out.Err(self.env,id,grpstr)
                        grpstr=s+'\n'
                else:
                    self.reporter.stderr(grpstr)
                    self.other_out.Err(self.env,id,grpstr)
            else:
                # we have some error or unknown code
                pass
        
class part_nil_logger:
    ''' the point of this class is to define the base interface for all part logger
    items. The goal is the this object is to be a empty object that can be written to
    in case that no other item is provided, or if logging is turned off'''
    def __init__(self):
        pass
    def Start(self,env,id,cmd):
        pass
    def End(self,env,id,exit_code):
        pass
    def Out(self,env,id,msg):
        pass
    def Err(self,env,id,msg):
        pass
        
        
class parts_text_logger:
    def __init__(self):
        self.m_file=None
        self.cache={}
        self.m_lock=thread.allocate_lock()
        
        
    def create_file(self,env):
        #The lock is needed here to prevent more than one thread creating this file
        # at the same time
        self.m_lock.acquire()
        if self.m_file == None:
            dr=env.Dir(env.subst("$LOG_PART_DIR")).abspath
            fn=env.subst("$LOG_PART_FILE_NAME")
            if os.path.exists(dr) == False:
                os.makedirs(dr)
            self.m_file=open(os.path.join(dr,fn),"w") 
        self.m_lock.release()
        
    def Start(self,env,id,cmd):
        self.create_file(env)
        if cmd[-1:]=='\n':
            eol=''
        else:
            eol='\n'
        self.cache[id]=[
            (console.Console.out_stream,'Task:'+cmd+eol),
            (console.Console.out_stream,"Output begin ----------------------------------------------------------------\n")
            ]
       
    def End(self,env,id,exit_code):
        s=""
        for text in self.cache[id]:
            if text[0] == console.Console.out_stream:
                s+=text[1]
            elif text[0] ==console.Console.error_stream:
                s+=text[1]
            else:
                # we have some error or unknown code
                pass
        s+="Output end   ----------------------------------------------------------------\n"
        s+="return code = "+str(exit_code)+"\n"
        self.m_file.write(s)
        del self.cache[id]
                
    def Out(self,env,id,msg):
        self.cache[id].append((console.Console.out_stream,msg))
        
    def Err(self,env,id,msg):
        self.cache[id].append((console.Console.error_stream,msg))
        
    def __del__(self):
        if self.__dict__.has_key('m_file') == False:
            return 
        for id in self.cache:
            self.cache[id].append((1,"Build interupted"))
            s=''
            for text in self.cache[id]:
                if text[0] == console.Console.out_stream:
                    s+=text[1]
                elif text[0] ==console.Console.error_stream:
                    s+=text[1]
                else:
                    # we have some error or unknown code
                    pass
            s+="] (return code = 1)\n"
            self.m_file.write(s)
        
        
common.AddVariable('PART_SPAWNER',part_spawner,'')        
common.AddVariable('PART_LOGGER','PART_NIL_LOGGER','')
common.AddVariable('PART_NIL_LOGGER',part_nil_logger,'')
common.AddVariable('PART_TEXT_LOGGER',parts_text_logger,'')
common.AddVariable('LOG_PART_DIR','${LOG_DIR}','')
common.AddVariable('LOG_PART_FILE_NAME','${PART_NAME}_${PART_VERSION}.log','')
