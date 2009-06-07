from parts.tools.Common.ToolSetting import *
from parts.tools.Common.ToolInfo import *
from parts.tools.Common.Finders import *
from parts.platform_info import *
import unittest




#### tests for TestSettings objects
class TestPathFinder(unittest.TestCase):

    def setUp(self):
        self.env=SCons.Script.Environment(tools=[],HOST_PLATFORM=HostSystem(),TARGET_PLATFORM=HostSystem())

    #clean up test here to make it portable
    def test_exists(self):

        ts=ToolSetting('cl')

        ts.Register(
            hosts=[SystemPlatform('win32','x86_64')],
            targets=[SystemPlatform('win32','x86_64')],
            info=[
                ToolInfo(
                    version='9.0',
                    install_scanner=[
                        PathFinder([
                        r'C:\Program Files (x86)\Microsoft Visual Studio 9.0',
                        r'C:\Program Files\Microsoft Visual Studio 9.0'
                        ])
                    ],
                    script=None,
                    subst_vars={},
                    shell_vars={'PATH':'${CL.INSTALL_ROOT}/VC/bin/amd64;${CL.INSTALL_ROOT}/VC/bin'},
                    test_file='amd64/cl.exe'
                    )
                ]
            )

        # should be True
        self.assertEqual(True,ts.Exists(self.env))
        #print ts.Exists(self.env)
        # should be False
        #print ts.Exists(self.env,TARGET_PLATFORM=SystemPlatform_config('win32','x86'))

    def test_get_latest(self):

        ts=ToolSetting('cl')

        ts.Register(
            hosts=[SystemPlatform('win32','x86_64')],
            targets=[SystemPlatform('win32','x86_64')],
            info=[
                ToolInfo(
                    version='11.1',
                    install_scanner=[
                        PathFinder([
                        r'C:\Program Files (x86)\Microsoft Visual Studio 9.0',
                        r'C:\Program Files\Microsoft Visual Studio 9.0'
                        ])
                    ],
                    script=None,
                    subst_vars={},
                    shell_vars={'PATH':'${CL.INSTALL_ROOT}/VC/bin'},
                    test_file='cl.exe'
                    ),
                ToolInfo(
                    version='10.0',
                    install_scanner=[
                        PathFinder([
                        r'C:\Program Files (x86)\Microsoft Visual Studio 9.0',
                        r'C:\Program Files\Microsoft Visual Studio 9.0'
                        ])
                    ],
                    script=None,
                    subst_vars={},
                    shell_vars={'PATH':'${CL.INSTALL_ROOT}/VC/bin'},
                    test_file='cl.exe'
                    ),
                ToolInfo(
                    version='1.1',
                    install_scanner=[
                        PathFinder([
                        r'C:\Program Files (x86)\Microsoft Visual Studio 9.0',
                        r'C:\Program Files\Microsoft Visual Studio 9.0'
                        ])
                    ],
                    script=None,
                    subst_vars={},
                    shell_vars={'PATH':'${CL.INSTALL_ROOT}/VC/bin'},
                    test_file='cl.exe'
                    ),
                ToolInfo(
                    version='11.0',
                    install_scanner=[
                        PathFinder([
                        r'C:\Program Files (x86)\Microsoft Visual Studio 9.0',
                        r'C:\Program Files\Microsoft Visual Studio 9.0'
                        ])
                    ],
                    script=None,
                    subst_vars={},
                    shell_vars={'PATH':'${CL.INSTALL_ROOT}/VC/bin'},
                    test_file='cl.exe'
                    ),
                ToolInfo(
                    version='1.0',
                    install_scanner=[
                        PathFinder([
                        r'C:\Program Files (x86)\Microsoft Visual Studio 9.0',
                        r'C:\Program Files\Microsoft Visual Studio 9.0'
                        ])
                    ],
                    script=None,
                    subst_vars={},
                    shell_vars={'PATH':'${CL.INSTALL_ROOT}/VC/bin'},
                    test_file='cl.exe'
                    ),
                
                ]
            )
        key=ts.get_cache_key(self.env)
        ts.query_for_known(self.env,key)
        # should be equal to 11.1
        #print ts.get_latest_known_version(key)

# tests for getting the enviroment
# we need to test many different cases

    def test_get_shell_env1(self):
        ts=ToolSetting('cl')

        ts.Register(
            hosts=[SystemPlatform('win32','x86_64')],
            targets=[SystemPlatform('win32','x86_64')],
            info=[
                ToolInfo(
                    version='9.0',
                    install_scanner=[
                        PathFinder([
                        r'C:\Program Files (x86)\Microsoft Visual Studio 9.0',
                        r'C:\Program Files\Microsoft Visual Studio 9.0'
                        ])
                    ],
                    script=None,
                    subst_vars={},
                    shell_vars={'PATH':'${CL.INSTALL_ROOT}\\VC\\bin'},
                    test_file='cl.exe'
                    )
                ]
            )
        #print ts.get_shell_env(self.env)
        
    def test_get_shell_env2(self):
        # tests that INSTALL_ROOT works
        ts=ToolSetting('cl')

        ts.Register(
            hosts=[SystemPlatform('win32','x86_64')],
            targets=[SystemPlatform('win32','x86_64')],
            info=[
                ToolInfo(
                    version='9.0',
                    install_scanner=[
                        PathFinder([
                        r'C:\Program Files (x86)\Microsoft Visual Studio 9.0',
                        r'C:\Program Files\Microsoft Visual Studio 9.0'
                        ])
                    ],
                    script=ScriptFinder('${CL.INSTALL_ROOT}/testvars.cmd','hello'),
                    subst_vars={},
                    shell_vars={'PATH':'${CL.INSTALL_ROOT}\\VC\\bin'},
                    test_file='cl.exe'
                    )
                ]
            )
        #print
        #print "1)",ts.get_shell_env(self.env.Clone(CL_INSTALL_ROOT=r'C:\Program Files (x86)\Microsoft Visual Studio 9.0'))
        #print "True=",ts.Exists(self.env.Clone(CL_INSTALL_ROOT=r'C:\Program Files (x86)\Microsoft Visual Studio 9.0'))
        #print "2)",ts.get_shell_env(self.env.Clone(CL_INSTALL_ROOT=r'.\testdata'))
        #print "True=",ts.Exists(self.env.Clone(CL_INSTALL_ROOT=r'.\testdata'))
        #print "False=",ts.Exists(self.env.Clone(CL_INSTALL_ROOT=r'C:\MYPATH'))
        #try:   
        #    print "3)",ts.get_shell_env(self.env.Clone(CL_INSTALL_ROOT=r'C:\MYPATH'))
        #except:
        #    pass
        #print "True=",ts.Exists(self.env.Clone(CL_INSTALL_ROOT=r'.\testdata',CL_SCRIPT=True))
        
        #print "4)",ts.get_shell_env(self.env.Clone(CL_INSTALL_ROOT=r'.\testdata',CL_SCRIPT=True))
        


