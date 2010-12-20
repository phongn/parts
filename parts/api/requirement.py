
from .. import common
from .. import policy

from ..requirement import DefineRequirementSet, requirement,REQ
          
# setup default value for common stuff... some of this should move to tools that define them

# general
DefineRequirementSet('EXISTS',[])

# C/C++ like
DefineRequirementSet('CPPPATH',[requirement('CPPPATH',public=True,policy=REQ.Policy.ignore)])
DefineRequirementSet('CPPDEFINES',[requirement('CPPDEFINES',public=True,policy=REQ.Policy.ignore)])
DefineRequirementSet('CXXFLAGS',[requirement('CXXFLAGS',public=True,policy=REQ.Policy.ignore)])
DefineRequirementSet('CFLAGS',[requirement('CFLAGS',public=True,policy=REQ.Policy.ignore)])
DefineRequirementSet('CCFLAGS',[requirement('CCFLAGS',public=True,policy=REQ.Policy.ignore)])
DefineRequirementSet('LINKFLAGS',[requirement('LINKFLAGS',public=True,policy=REQ.Policy.ignore)])
DefineRequirementSet('LIBPATH',[requirement('LIBPATH',public=True,policy=REQ.Policy.ignore)])

DefineRequirementSet('HEADERS',['CPPPATH','CPPDEFINES'],weight=-5000)
DefineRequirementSet('LIBS',['LIBPATH',requirement('LIBS',public=True,policy=REQ.Policy.ignore,mapper='PARTEXPORTLIB',listtype=True)],weight=-5000)

DefineRequirementSet('CPP_DEFAULTS',['LIBS','HEADERS'],weight=-9000)
DefineRequirementSet('C_DEFAULTS',['LIBS','HEADERS'],weight=-9000)

# defaults
DefineRequirementSet('DEFAULT',['CPP_DEFAULTS','C_DEFAULTS'],weight=-10000)

# stuff to remove
DefineRequirementSet('ALL_DEFAULT',['LIBS','HEADERS','CCFLAGS','CFLAGS','CXXFLAGS'],policy.ReportingPolicy.warning,weight=-999999)
