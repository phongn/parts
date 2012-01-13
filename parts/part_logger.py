import glb
import common
import console 
import api.output
import version

import subprocess,sys,string,os
import thread,threading

import SCons.Script

import platform

pyver=version.version(platform.python_version())

class pipeRedirector(object):
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

class part_spawner(object):
    def __init__(self,env):
        self.env=env   

    def __call__(self,shell, escape, cmd, args, Env):
        # setup the call        
        
        ENV={}
        for k,v in Env.iteritems():
            ENV[k]=str(v)
        # get the part_logger
        output=self.env["PART_LOG_MAPPER"]
        
        # we ignore the escape function as it breaks linux, 
        # and was breaking on python 2.7 windows by adding extra " values
        # ie '"c:\program file\x.exe" foo bar"' -> '""c:\program file\x.exe" foo bar""'
        # we assume the command has "quotes" around it as need
        if pyver < '2.7' and sys.platform == 'win32':
            command_line = escape(string.join(args))
        else:
            command_line = string.join(args)
        
        #tell it we are starting a given action/command, get action_id        
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



class part_logger(object):
    def __init__(self,env,console):
        self.env=env
        def_env=SCons.Script.DefaultEnvironment()
        self.reporter=glb.rpter
        tmp=SCons.Script.GetOption('num_jobs') > 1
        if tmp:
            self.block_text=2 # partial blocking of text
        else:
            self.block_text=0 # no blocking of text
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
        try:
            del self.cache[id]
        except KeyError:
            pass

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
        testlst=self.cache[id]
        self.cache[id]=[]
        for text in testlst:
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
        

class part_nil_logger(object):
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
    def TaskStart(self,msg):
        pass
    def TaskEnd(self,id,exit_code):
        pass
    def WriteOut(self,id,msg):
       pass
    def WriteErr(self,id,msg):
       pass 
        
class parts_text_logger(object):
    def __init__(self):
        self.m_file=None
        self.cache={}
        self.m_lock=thread.allocate_lock()
        
        
    def create_file(self,env):
        #The lock is needed here to prevent more than one thread creating this file
        # at the same time
        self.m_lock.acquire()
        if self.m_file is None:
            dr=env.Dir(env.subst("$LOG_PART_DIR")).abspath
            fn=env.subst("$LOG_PART_FILE_NAME")
            if os.path.exists(dr) == False:
                os.makedirs(dr)
            self.fname=os.path.join(dr,fn)
            self.m_file=open(os.path.join(dr,fn),"w") 
            self.m_file.close() # part of quick "to many file handle" fix
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
        self.m_lock.acquire()# part of quick "to many file handle" fix
        self.m_file=open(self.fname,"a+") # part of quick "to many file handle" fix
        self.m_file.write(s)
        self.m_file.close() # part of quick "to many file handle" fix
        self.m_lock.release()# part of quick "to many file handle" fix
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
            
            self.m_lock.acquire()# part of quick "to many file handle" fix
            self.m_file=open(self.fname,"a+") # part of quick "to many file handle" fix
            self.m_file.write(s)
            self.m_file.close() # part of quick "to many file handle" fix
            self.m_lock.release()# part of quick "to many file handle" fix
        
        
api.register.add_variable('PART_SPAWNER',part_spawner,'')        
api.register.add_variable('PART_LOGGER','PART_NIL_LOGGER','')
api.register.add_variable('PART_NIL_LOGGER',part_nil_logger,'')
api.register.add_variable('PART_TEXT_LOGGER',parts_text_logger,'')
api.register.add_variable('LOG_PART_DIR','${LOG_DIR}','')
api.register.add_variable('LOG_PART_FILE_NAME','${PART_NAME}_${PART_VERSION}.log','')
