
from .. import common
import platforms
import requirement


# core API

def add_section(section):
    ''' 
    Called to add a new section type
    
    @param section The mapper object to add globally
    
    '''
    common.g_sections.add(section)
    
def add_mapper(mapper):
    '''
    Called to add a new mapper object
    
    @param mapper The mapper object to add globally
    
    '''
    common.g_mappers[mapper.name]=mapper

def add_global_parts_object(key,object,map_env=False):
    '''
    Called to add a function or object at a global "part file" scope
    
    @param key The value the object will be seen as by the user
    @param object The object we want to add
    @param map_env Map the object with env instance that will passed to the user. 
    
    If map_env is true the object as to be a class. the setup code will create an 
    instance that will have the __init__ passed env as the only argument, for it to store
    when the calls an API or __call__ method.
    '''
    if map_env:
        common.g_parts_objs_env[key]=object
    else:
        common.g_parts_objs[key]=object
    
def add_global_sconstruct_object(key,object):
    '''
    Called to add an object at a global Sconstruct level
    
    @param key The value the object will be seen as by the user
    @param object The object we want to add
    '''
    common.g_globals[key]=object

def add_builder(name,builder):
    if common.g_builders.has_key(name)==False:
        common.g_builders[name]=builder
    else:
        reporter.report_warning('Builder "{0}" was already defined. Ignoring new definition.'.format(name),show_stack=False)


