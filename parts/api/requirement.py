
from .. import common
from .. import policy

from ..requirement import DefineRequirementSet, requirement,REQ
          
# setup default value for common stuff... some of this should move to tools that define them

# general


#general SDK
DefineRequirementSet('SDKINCLUDE',[requirement('SDKINCLUDE',policy=REQ.Policy.ignore,listtype=True)])
DefineRequirementSet('SDKLIB',[requirement('SDKLIB',policy=REQ.Policy.ignore,listtype=True)])
DefineRequirementSet('SDKBIN',[requirement('SDKBIN',policy=REQ.Policy.ignore,listtype=True)])
DefineRequirementSet('SDKCONFIG',[requirement('SDKCONFIG',policy=REQ.Policy.ignore,listtype=True)])
DefineRequirementSet('SDKDOC',[requirement('SDKDOC',policy=REQ.Policy.ignore,listtype=True)])
DefineRequirementSet('SDKHELP',[requirement('SDKHELP',policy=REQ.Policy.ignore,listtype=True)])
DefineRequirementSet('SDKMANPAGE',[requirement('SDKMANPAGE',policy=REQ.Policy.ignore,listtype=True)])
DefineRequirementSet('SDKDATA',[requirement('SDKDATA',policy=REQ.Policy.ignore,listtype=True)])
DefineRequirementSet('SDKMESSAGE',[requirement('SDKMESSAGE',policy=REQ.Policy.ignore,listtype=True)])
DefineRequirementSet('SDKRESOURCE',[requirement('SDKRESOURCE',policy=REQ.Policy.ignore,listtype=True)])
DefineRequirementSet('SDKSAMPLE',[requirement('SDKSAMPLE',policy=REQ.Policy.ignore,listtype=True)])
DefineRequirementSet('SDKTOPLEVEL',[requirement('SDKTOPLEVEL',policy=REQ.Policy.ignore,listtype=True)])
DefineRequirementSet('SDKPKGNO',[requirement('SDKPKGNO',policy=REQ.Policy.ignore,listtype=True)])
DefineRequirementSet('SDKAPI',[requirement('SDKAPI',policy=REQ.Policy.ignore,listtype=True)])
DefineRequirementSet('SDKPYTHON',[requirement('SDKPYTHON',policy=REQ.Policy.ignore,listtype=True)])
DefineRequirementSet('SDKSCRIPT',[requirement('SDKSCRIPT',policy=REQ.Policy.ignore,listtype=True)])

DefineRequirementSet('SDKTARGET',['SDKBIN','SDKLIB'],weight=-5000)
DefineRequirementSet('SDKFILES',[
                        'SDKINCLUDE',
                        'SDKLIB',
                        'SDKBIN',
                        'SDKCONFIG',
                        'SDKDOC',
                        'SDKHELP',
                        'SDKMANPAGE',
                        'SDKDATA',
                        'SDKMESSAGE',
                        'SDKRESOURCE',
                        'SDKSAMPLE',
                        'SDKTOPLEVEL',
                        'SDKPKGNO',
                        'SDKAPI',
                        'SDKPYTHON',
                        'SDKSCRIPT'
                        ],weight=-5000)

#general install
DefineRequirementSet('INSTALLINCLUDE',[requirement('INSTALLINCLUDE',policy=REQ.Policy.ignore,listtype=True)])
DefineRequirementSet('INSTALLLIB',[requirement('INSTALLLIB',policy=REQ.Policy.ignore,listtype=True)])
DefineRequirementSet('INSTALLBIN',[requirement('INSTALLBIN',policy=REQ.Policy.ignore,listtype=True)])
DefineRequirementSet('INSTALLCONFIG',[requirement('INSTALLCONFIG',policy=REQ.Policy.ignore,listtype=True)])
DefineRequirementSet('INSTALLDOC',[requirement('INSTALLDOC',policy=REQ.Policy.ignore,listtype=True)])
DefineRequirementSet('INSTALLHELP',[requirement('INSTALLHELP',policy=REQ.Policy.ignore,listtype=True)])
DefineRequirementSet('INSTALLMANPAGE',[requirement('INSTALLMANPAGE',policy=REQ.Policy.ignore,listtype=True)])
DefineRequirementSet('INSTALLDATA',[requirement('INSTALLDATA',policy=REQ.Policy.ignore,listtype=True)])
DefineRequirementSet('INSTALLMESSAGE',[requirement('INSTALLMESSAGE',policy=REQ.Policy.ignore,listtype=True)])
DefineRequirementSet('INSTALLRESOURCE',[requirement('INSTALLRESOURCE',policy=REQ.Policy.ignore,listtype=True)])
DefineRequirementSet('INSTALLSAMPLE',[requirement('INSTALLSAMPLE',policy=REQ.Policy.ignore,listtype=True)])
DefineRequirementSet('INSTALLTOPLEVEL',[requirement('INSTALLTOPLEVEL',policy=REQ.Policy.ignore,listtype=True)])
DefineRequirementSet('INSTALLPKGNO',[requirement('INSTALLPKGNO',policy=REQ.Policy.ignore,listtype=True)])
DefineRequirementSet('INSTALLAPI',[requirement('INSTALLAPI',policy=REQ.Policy.ignore,listtype=True)])
DefineRequirementSet('INSTALLPYTHON',[requirement('INSTALLPYTHON',policy=REQ.Policy.ignore,listtype=True)])
DefineRequirementSet('INSTALLSCRIPT',[requirement('INSTALLSCRIPT',policy=REQ.Policy.ignore,listtype=True)])

DefineRequirementSet('INSTALLTARGET',['INSTALLBIN','INSTALLLIB'],weight=-5000)
DefineRequirementSet('INSTALLFILES',[
                        'INSTALLINCLUDE',
                        'INSTALLLIB',
                        'INSTALLBIN',
                        'INSTALLCONFIG',
                        'INSTALLDOC',
                        'INSTALLHELP',
                        'INSTALLMANPAGE',
                        'INSTALLDATA',
                        'INSTALLMESSAGE',
                        'INSTALLRESOURCE',
                        'INSTALLSAMPLE',
                        'INSTALLTOPLEVEL',
                        'INSTALLPKGNO',
                        'INSTALLAPI',
                        'INSTALLPYTHON',
                        'INSTALLSCRIPT'
                        ],weight=-5000)

DefineRequirementSet('EXISTS',['INSTALLFILES'])

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
DefineRequirementSet('DEFAULT',['CPP_DEFAULTS','C_DEFAULTS','INSTALLFILES','SDKLIB','SDKBIN'],weight=-10000)

# stuff to remove
DefineRequirementSet('ALL_DEFAULT',['LIBS','HEADERS','CCFLAGS','CFLAGS','CXXFLAGS'],policy.ReportingPolicy.warning,weight=-999999)
