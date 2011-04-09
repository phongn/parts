## the core logic
#to be removed
    





#
#def get_file_main_script(def_env):
#    if def_env.GetOption('file')!=[]:
#        return ''
#    if os.path.exists('SConstruct'):
#        return 'SConstruct'
#    if os.path.exists('Sconstruct'):
#        return 'SConstruct'
#    if os.path.exists('sconstruct'):
#        return 'SConstruct'
#    return ''
#
#    
#
#import time
#def part_object_setup():
#    api.output.print_msg("Processing Part objects")
#    total_file_install=0
#    total_file_build=0
#    total_parts=0
#    total_subparts=0
#    total_src=0
#    total_nodes=0
#    for i in glb.parts.keys():
#        api.output.print_msg("Processing Part:", i)
#        tmp=glb.parts[i]
#        start=time.time()
#        #tmp.Process()
#        total_file_build += len(tmp.target_files)
#        total_file_install += len(tmp.installed_files)
#        total_parts+=1
#        total_src+= len(tmp.source_files)
#        total_nodes= total_src+total_file_build
#        print "*****", tmp.alias,time.time()-start
#        print 'tally total_parts',total_parts
#        print 'tally total_subparts',total_subparts
#        print 'tally total_file_build',total_file_build
#        print 'tally total_file_install',total_file_install
#        print 'tally total_src',total_src
#        print 'tally total_nodes',total_nodes
#        for sub in tmp.sub_parts.values():
#            total_file_build += len(sub.target_files)
#            total_file_install += len(sub.installed_files)
#            total_parts+=1
#            total_subparts+=1
#            print '---',sub.alias
#            print 'tally total_parts',total_parts
#            print 'tally total_subparts',total_subparts
#            print 'tally total_file_build',total_file_build
#            print 'tally total_file_install',total_file_install
#            print 'tally total_src',total_src
#            print 'tally total_nodes',total_nodes
#        
#        #print "end",i
#    print 'total_parts',total_parts
#    print 'total_subparts',total_subparts
#    print 'total_file_build',total_file_build
#    print 'total_file_install',total_file_install
#    print 'total_src',total_src
#    print 'total_nodes',total_nodes
#    api.output.print_msg("Finished processing Part objects")
#
#
#
## This is what we want to be setup in parts
#from SCons.Script.SConscript import SConsEnvironment
#
#api.register.add_bool_variable('REBUILD_ALL',False,'')
#