
def default_test_func(self,*lst,**kw):
	for l in lst:
		if callable(l):
			if l(self.env) == False:
				return False
		else:
			#error.. must be a callable type
			pass
			
	for k,v in kw.items():
		try:
			if not (self.env[k]==v):
				return False
		except KeyError:
			return False
	return True


class section(object):
    ''' this class allows for the creation of a "Section" in the Parts file
    A section is a set of functions or phases that are used to setup state to 
    do some set of actions. The main difference over the classic functional way
    is that this allow control over the processing of section or phases based on 
    the target value and otehr logic tha section can define in how it processed 
    the different phases.
    '''
    def __init__(self,name,processfunc,concepts_namspaces):
        '''
        name-- is the name of the section
        processfunc-- is a function(...) that will be called to process the 
        section by the part manger object
        concept_namespaces-- is a list of namespaces that will be made to bind
        this section with a global target
        '''
        self.dict={
                '_phases':[],
                #'Process':processfunc
                }
        self.name=name
        self.concepts=concepts_namspaces
        self.processfunc=processfunc
        
    def AddPhase(self,name,test_func=None,optional=False):
        '''
        This function will define a new phase for a given section
        name-- is the name of phase
        test_func-- is an optional function that will test attribute for seeing
        if this "case" shoudl be processed
        optional-- tells that this phase does not have to be defined to have a fully
        valid section
        '''
    
        def _phase(self,func,*lst,**kw):
            # allows us to make sure this function was only processed once after it has passed
            # this is faster than doing the full test if we know we can skip out
            if func.__dict__.get("parts_processed_passed",False)==True:
                return func 
            if getattr(self,'test_'+name)(*lst,**kw):
                getattr(self,'func_'+name).append(func)
                func.parts_processed_passed=True
            return func
        
        def phase(self,func=None,*lst,**kw):
            if func is None:
                # return lamda function ( arg where passed in)
                return lambda x: getattr(self,'__'+name)(x,*lst,**kw)
            else:
                # return result of function call ( no args where passed in)
                return getattr(self,'__'+name)(func,*lst,**kw)
        
        if test_func is None:
            test_func=default_test_func
        
        # add phase data list
        self.dict['_phases'].append((name,optional))
        #add the function
        self.dict["test_"+name]=test_func
        self.dict["__"+name]=_phase
        self.dict[name]=phase
        

    def Type(self):
        if hasattr(self.Type.im_func,'type')==False:
            class mybase(object):
                def __init__(self,env):
                    self.passed=False # this allow us to skip tests if we have stacked declorators
                    self.env=env
                    for p in self._phases:
                        setattr(self,"func_"+p[0],[])
                
                def isSet(self):
                    for p in self._phases:
                        # we want to find a phase that was set
                        if getattr(self,"func_"+p[0],[]) != []:
                            return True
                    return False
                
                def isValid(self):
                    for p in self._phases:
                        # if value not set and it is not option
                        if getattr(self,"func_"+p[0],[]) == [] and p[1] == False:
                            return False
                    return True
                
                def FoundPhases(self):
                    ret=[]
                    for p in self._phases:
                        # we want phases that are called
                        if getattr(self,"func_"+p[0],[]) != [] :
                            ret.append(p[0])
                    return ret
                
                def RequiredPhases(self):
                    ret=[]
                    for p in self._phases:
                        # we want items that are not options
                        if p[1] == False:
                            ret.append(p[0])
                    return ret
                
                        
            self.Type.im_func.type=mybase.__class__('%sSectionType'%self.name, (mybase,), self.dict)
            
            
        return self.Type.im_func.type
    def GetHandler(self):
        return self.processfunc
        
    def HandleConcept(self,name):
        if name in self.concepts:
            return True
        return False



