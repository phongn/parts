import sys
import common
import console

class streamer:
    def __init__(self,outfunc):
        self.outfunc=outfunc
    def write(self,str):
        self.outfunc(msg=str)
    def flush(self):
        pass
    

class reporter:
    def __init__(self,logger,silent,wrn_as_err=False):
        sys.stdout=streamer(self.stdout)
        sys.stderr=streamer(self.stderr)
        
        self.console=console.Console(wrn_as_err)
        self.logger=logger
        self.already_printed = set()
        self.silent=silent
    
    def part_warning(self,env,msg,print_once=False):
        s="Parts: Warning : "+msg+"\n"
        #s='Parts: Warning : %s(%d) : %s\n' % (caller_frame[1], caller_frame[2], msg)

        if type(env) is not type(None):
            s= 'Parts: Warning : In %s : %s\n' % (env.subst(env.get("PART_FILE","unknown file")), msg)
            s+="        Processing PART_NAME=["+env.subst(env.get("PART_NAME","unknown name"))+"]\n"
            s+="        Processing PART_VERSION=["+env.subst(env.get("PART_VERSION","unknown version"))+"]\n"
            s+="        Processing PART_ALIAS=["+env.subst(env.get("PART_ALIAS","unknown alias"))+"]\n"
        
        if print_once ==True:
            if hash(s) not in self.already_printed:
                self.already_printed.add(hash(s))
            else:
                return
        self.console.Warning.Write(s)
        self.logger.logwrn(s)
        
    def part_error(self,env,msg):
        s="Parts: ERROR! : "+msg+"\n"
        
        if type(env) is not type(None):
            s= 'Parts: ERROR! : In %s : %s\n' % (env.subst(env.get("PART_FILE","unknown file")), msg)
            s+="        Processing PART_NAME=["+env.subst(env.get("PART_NAME","unknown name"))+"]\n"
            s+="        Processing PART_VERSION=["+env.subst(env.get("PART_VERSION","unknown version"))+"]\n"
            s+="        Processing PART_ALIAS=["+env.subst(env.get("PART_ALIAS","unknown alias"))+"]\n"
        
        self.console.Error.Write(s)
        self.logger.logerr(s)
        
    def part_message(self,msg):
        if self.silent ==False:
            s="Parts: "+msg+"\n"
            self.console.Write(s)
            self.logger.log(s)
            
    def verbose_msg(self,catagory,msg):
        pass
    
    def stdout(self,msg):
        '''This function gets all redirected stdout text from random print calls'''
        self.console.Write(msg)
        self.logger.log(msg)
         
    def stderr(self,msg):
        '''This will gets any stderr text in scons via a print>>stderr usage'''
        self.console.Error.Write(msg)
        self.logger.logerr(msg)
    
    def stdwrn(self,msg):
        '''Unlike stdout and stderr, stdwrn doesn't really exist.. but we use
        this to pass text that is in a warning state from with in parts'''
        self.console.Warning.Write(msg)
        self.logger.logwrn(msg)
        



common.AddBoolVariable('STREAM_WARNING_AS_ERROR',False, 'Controls is warning based messages are treated as errors')
