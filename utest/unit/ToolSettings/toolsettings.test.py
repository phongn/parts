import sys
from parts.tools.Common.ToolSetting import *
from parts.tools.Common.ToolInfo import *
from parts.tools.Common.Finders import *
from parts.platform_info import *
import unittest


is_win32=False
is_linux=False
if sys.platform == 'win32':
    is_win32=True
elif sys.platform.startswith('linux'):
    is_linux=True

#tests for ToolSettings objects
class TestToolSettings(unittest.TestCase):

    def setUp(self):
        self.env=SCons.Script.Environment(tools=[],HOST_PLATFORM=HostSystem(),TARGET_PLATFORM=HostSystem())


    if is_win32:

        def test_exists(self):
            """Creates dummy tool 'mycl' and tests that it exists for specified platform"""
            ts=ToolSetting('mycl')

            ts.Register(
                hosts=[SystemPlatform('win32','x86_64')],
                targets=[SystemPlatform('win32','x86_64')],
                info=[
                    ToolInfo(
                        version='0.0',
                        install_scanner=[PathFinder([r'./testdata'])],
                        script=None,
                        subst_vars={},
                        shell_vars={'PATH': r'./testdata/vc/bin'},
                        test_file='cl.exe'
                        )
                    ]
                )

            self.assertEqual(True, ts.Exists(self.env))
            self.assertEqual(False, ts.Exists(self.env,TARGET_PLATFORM=SystemPlatform('win32','x86')))

        def test_get_latest_known_version1(self):
            """Creates dummy tool 'mycl' with versions 0.0 and 1.0, query for exact 0.0 version and tests that exactly this version is found"""
            ts=ToolSetting('mycl')

            ts.Register(
                hosts=[SystemPlatform('win32','x86_64')],
                targets=[SystemPlatform('win32','x86_64')],
                info=[
                    ToolInfo(
                        version='0.0',
                        install_scanner=[PathFinder([r'./testdata'])],
                        script=None,
                        subst_vars={},
                        shell_vars={'PATH': r'./testdata/vc/bin'},
                        test_file='cl.exe'
                        ),
                    ToolInfo(
                        version='1.0',
                        install_scanner=[PathFinder([r'./testdata'])],
                        script=None,
                        subst_vars={},
                        shell_vars={'PATH': r'./testdata/vc/bin'},
                        test_file='cl.exe'
                        ),
                    ]
                )

            key = ts.get_cache_key(self.env)
            ts.query_for_exact(self.env, key, '0.0')
            self.assertEqual('0.0', ts.get_latest_known_version(key))

        def test_get_latest_known_version2(self):
            """Creates dummy tool 'mycl' with versions 0.0 and 1.0, query for known version and tests that the latest 1.0 version is found"""
            ts=ToolSetting('mycl')

            ts.Register(
                hosts=[SystemPlatform('win32','x86_64')],
                targets=[SystemPlatform('win32','x86_64')],
                info=[
                    ToolInfo(
                        version='0.0',
                        install_scanner=[PathFinder([r'./testdata'])],
                        script=None,
                        subst_vars={},
                        shell_vars={'PATH': r'./testdata/vc/bin'},
                        test_file='cl.exe'
                        ),
                    ToolInfo(
                        version='1.0',
                        install_scanner=[PathFinder([r'./testdata'])],
                        script=None,
                        subst_vars={},
                        shell_vars={'PATH': r'./testdata/vc/bin'},
                        test_file='cl.exe'
                        ),
                    ]
                )

            key = ts.get_cache_key(self.env)
            ts.query_for_known(self.env, key)
            self.assertEqual('1.0', ts.get_latest_known_version(key))

        def test_get_shell_env1(self):
            """Creates dummy tool 'mycl' and tests that tool environment has proper env variables set: 'INSTALL_ROOT', 'TOOL' and 'VERSION'"""
            ts=ToolSetting('mycl')

            ts.Register(
                hosts=[SystemPlatform('win32','x86_64')],
                targets=[SystemPlatform('win32','x86_64')],
                info=[
                    ToolInfo(
                        version='0.0',
                        install_scanner=[PathFinder([r'./testdata'])],
                        script=None,
                        subst_vars={},
                        shell_vars={'PATH': r'./testdata/vc/bin'},
                        test_file='cl.exe'
                        )
                    ]
                )

            shellEnv, tsEnv = ts.get_shell_env(self.env)
            self.assertEqual(tsEnv['INSTALL_ROOT'], 'testdata')
            self.assertEqual(tsEnv['TOOL'], 'cl.exe')
            self.assertEqual(tsEnv['VERSION'], '0.0')

    elif is_linux:

        def test_exists(self):
            """Creates dummy tool 'mycl' and tests that it exists for specified platform"""
            ts=ToolSetting('mycl')

            ts.Register(
                hosts=[SystemPlatform('posix','x86_64')],
                targets=[SystemPlatform('posix','x86_64')],
                info=[
                    ToolInfo(
                        version='0.0',
                        install_scanner=[PathFinder([r'./testdata'])],
                        script=None,
                        subst_vars={},
                        shell_vars={'PATH': r'./testdata/vc/bin'},
                        test_file='cl.exe'
                        )
                    ]
                )

            self.assertEqual(True, ts.Exists(self.env))
            self.assertEqual(False, ts.Exists(self.env,TARGET_PLATFORM=SystemPlatform('posix','x86')))

        def test_get_latest_known_version1(self):
            """Creates dummy tool 'mycl' with versions 0.0 and 1.0, query for exact 0.0 version and tests that exactly this version is found"""
            ts=ToolSetting('mycl')

            ts.Register(
                hosts=[SystemPlatform('posix','x86_64')],
                targets=[SystemPlatform('posix','x86_64')],
                info=[
                    ToolInfo(
                        version='0.0',
                        install_scanner=[PathFinder([r'./testdata'])],
                        script=None,
                        subst_vars={},
                        shell_vars={'PATH': r'./testdata/vc/bin'},
                        test_file='cl.exe'
                        ),
                    ToolInfo(
                        version='1.0',
                        install_scanner=[PathFinder([r'./testdata'])],
                        script=None,
                        subst_vars={},
                        shell_vars={'PATH': r'./testdata/vc/bin'},
                        test_file='cl.exe'
                        ),
                    ]
                )

            key = ts.get_cache_key(self.env)
            ts.query_for_exact(self.env, key, '0.0')
            self.assertEqual('0.0', ts.get_latest_known_version(key))

        def test_get_latest_known_version2(self):
            """Creates dummy tool 'mycl' with versions 0.0 and 1.0, query for known version and tests that the latest 1.0 version is found"""
            ts=ToolSetting('mycl')

            ts.Register(
                hosts=[SystemPlatform('posix','x86_64')],
                targets=[SystemPlatform('posix','x86_64')],
                info=[
                    ToolInfo(
                        version='0.0',
                        install_scanner=[PathFinder([r'./testdata'])],
                        script=None,
                        subst_vars={},
                        shell_vars={'PATH': r'./testdata/vc/bin'},
                        test_file='cl.exe'
                        ),
                    ToolInfo(
                        version='1.0',
                        install_scanner=[PathFinder([r'./testdata'])],
                        script=None,
                        subst_vars={},
                        shell_vars={'PATH': r'./testdata/vc/bin'},
                        test_file='cl.exe'
                        ),
                    ]
                )

            key = ts.get_cache_key(self.env)
            ts.query_for_known(self.env, key)
            self.assertEqual('1.0', ts.get_latest_known_version(key))

        def test_get_shell_env1(self):
            """Creates dummy tool 'mycl' and tests that tool environment has proper env variables set: 'INSTALL_ROOT', 'TOOL' and 'VERSION'"""
            ts=ToolSetting('mycl')

            ts.Register(
                hosts=[SystemPlatform('posix','x86_64')],
                targets=[SystemPlatform('posix','x86_64')],
                info=[
                    ToolInfo(
                        version='0.0',
                        install_scanner=[PathFinder([r'./testdata'])],
                        script=None,
                        subst_vars={},
                        shell_vars={'PATH': r'./testdata/vc/bin'},
                        test_file='cl.exe'
                        )
                    ]
                )

            shellEnv, tsEnv = ts.get_shell_env(self.env)
            self.assertEqual(tsEnv['INSTALL_ROOT'], 'testdata')
            self.assertEqual(tsEnv['TOOL'], 'cl.exe')
            self.assertEqual(tsEnv['VERSION'], '0.0')


    def test_MatchVersionNumbers(self):
        """Test MatchVersionNumbers. Create various version strings including major, minor, revision numbers etc."""
        self.assertEqual(MatchVersionNumbers('1.1', '1.1.-1'), True)
        self.assertEqual(MatchVersionNumbers('1.2.3', '1'), True)
        self.assertEqual(MatchVersionNumbers('1.2.3', '1.2'), True)
        self.assertEqual(MatchVersionNumbers('1.2.3', '1.2.3'), True)
        self.assertEqual(MatchVersionNumbers('1.2.3', '1.2.3.4'), True)
        self.assertEqual(MatchVersionNumbers('1.2.3.', '1.2.3.4'), True)
        self.assertEqual(MatchVersionNumbers('1.2.3.4.', '1.2.3.4'), True)
        self.assertEqual(MatchVersionNumbers('1.2.3.4', '1.2.3.5'), True)

        self.assertEqual(MatchVersionNumbers('1.2', '12'), False)
        self.assertEqual(MatchVersionNumbers('1.2', '1.3'), False)
        self.assertEqual(MatchVersionNumbers('1.2.3', '1.2.4'), False)

        # This code raises the Exception in MatchVersionNumbers. I believe that
        # MatchVersionNumbers should handle the Exception and return True/False
        #try:
        self.assertEqual(MatchVersionNumbers('1.', '1'), True)
        #except:
        #    pass

        # This code raises the Exception in MatchVersionNumbers. I believe that
        # MatchVersionNumbers should handle the Exception and return True/False
        #try:
        self.assertEqual(MatchVersionNumbers('1.', '1.1'), False)
        #except:
        #    pass


#### tests for TestSettings objects
##class TestToolSettings(unittest.TestCase):
##
##    def setUp(self):
##        self.env=SCons.Script.Environment(tools=[],HOST_PLATFORM=HostSystem(),TARGET_PLATFORM=HostSystem())
##
##    #clean up test here to make it portable
##    def test_exists(self):
##
##        ts=ToolSetting('cl')
##
##        ts.Register(
##            hosts=[SystemPlatform('win32','x86_64')],
##            targets=[SystemPlatform('win32','x86_64')],
##            info=[
##                ToolInfo(
##                    version='9.0',
##                    install_scanner=[
##                        PathFinder([
##                        r'C:\Program Files (x86)\Microsoft Visual Studio 9.0',
##                        r'C:\Program Files\Microsoft Visual Studio 9.0'
##                        ])
##                    ],
##                    script=None,
##                    subst_vars={},
##                    shell_vars={'PATH':'${CL.INSTALL_ROOT}/VC/bin/amd64;${CL.INSTALL_ROOT}/VC/bin'},
##                    test_file='amd64/cl.exe'
##                    )
##                ]
##            )
##
##        # should be True
##        self.assertEqual(True,ts.Exists(self.env))
##        #print ts.Exists(self.env)
##        # should be False
##        #print ts.Exists(self.env,TARGET_PLATFORM=SystemPlatform_config('win32','x86'))
##
##    def test_get_latest(self):
##
##        ts=ToolSetting('cl')
##
##        ts.Register(
##            hosts=[SystemPlatform('win32','x86_64')],
##            targets=[SystemPlatform('win32','x86_64')],
##            info=[
##                ToolInfo(
##                    version='11.1',
##                    install_scanner=[
##                        PathFinder([
##                        r'C:\Program Files (x86)\Microsoft Visual Studio 9.0',
##                        r'C:\Program Files\Microsoft Visual Studio 9.0'
##                        ])
##                    ],
##                    script=None,
##                    subst_vars={},
##                    shell_vars={'PATH':'${CL.INSTALL_ROOT}/VC/bin'},
##                    test_file='cl.exe'
##                    ),
##                ToolInfo(
##                    version='10.0',
##                    install_scanner=[
##                        PathFinder([
##                        r'C:\Program Files (x86)\Microsoft Visual Studio 9.0',
##                        r'C:\Program Files\Microsoft Visual Studio 9.0'
##                        ])
##                    ],
##                    script=None,
##                    subst_vars={},
##                    shell_vars={'PATH':'${CL.INSTALL_ROOT}/VC/bin'},
##                    test_file='cl.exe'
##                    ),
##                ToolInfo(
##                    version='1.1',
##                    install_scanner=[
##                        PathFinder([
##                        r'C:\Program Files (x86)\Microsoft Visual Studio 9.0',
##                        r'C:\Program Files\Microsoft Visual Studio 9.0'
##                        ])
##                    ],
##                    script=None,
##                    subst_vars={},
##                    shell_vars={'PATH':'${CL.INSTALL_ROOT}/VC/bin'},
##                    test_file='cl.exe'
##                    ),
##                ToolInfo(
##                    version='11.0',
##                    install_scanner=[
##                        PathFinder([
##                        r'C:\Program Files (x86)\Microsoft Visual Studio 9.0',
##                        r'C:\Program Files\Microsoft Visual Studio 9.0'
##                        ])
##                    ],
##                    script=None,
##                    subst_vars={},
##                    shell_vars={'PATH':'${CL.INSTALL_ROOT}/VC/bin'},
##                    test_file='cl.exe'
##                    ),
##                ToolInfo(
##                    version='1.0',
##                    install_scanner=[
##                        PathFinder([
##                        r'C:\Program Files (x86)\Microsoft Visual Studio 9.0',
##                        r'C:\Program Files\Microsoft Visual Studio 9.0'
##                        ])
##                    ],
##                    script=None,
##                    subst_vars={},
##                    shell_vars={'PATH':'${CL.INSTALL_ROOT}/VC/bin'},
##                    test_file='cl.exe'
##                    ),
##
##                ]
##            )
##        key=ts.get_cache_key(self.env)
##        ts.query_for_known(self.env,key)
##        # should be equal to 11.1
##        #print ts.get_latest_known_version(key)
##
### tests for getting the enviroment
### we need to test many different cases
##
##    def test_get_shell_env1(self):
##        ts=ToolSetting('cl')
##
##        ts.Register(
##            hosts=[SystemPlatform('win32','x86_64')],
##            targets=[SystemPlatform('win32','x86_64')],
##            info=[
##                ToolInfo(
##                    version='9.0',
##                    install_scanner=[
##                        PathFinder([
##                        r'C:\Program Files (x86)\Microsoft Visual Studio 9.0',
##                        r'C:\Program Files\Microsoft Visual Studio 9.0'
##                        ])
##                    ],
##                    script=None,
##                    subst_vars={},
##                    shell_vars={'PATH':'${CL.INSTALL_ROOT}\\VC\\bin'},
##                    test_file='cl.exe'
##                    )
##                ]
##            )
##        #print ts.get_shell_env(self.env)
##
##    def test_get_shell_env2(self):
##        # tests that INSTALL_ROOT works
##        ts=ToolSetting('cl')
##
##        ts.Register(
##            hosts=[SystemPlatform('win32','x86_64')],
##            targets=[SystemPlatform('win32','x86_64')],
##            info=[
##                ToolInfo(
##                    version='9.0',
##                    install_scanner=[
##                        PathFinder([
##                        r'C:\Program Files (x86)\Microsoft Visual Studio 9.0',
##                        r'C:\Program Files\Microsoft Visual Studio 9.0'
##                        ])
##                    ],
##                    script=ScriptFinder('${CL.INSTALL_ROOT}/testvars.cmd','hello'),
##                    subst_vars={},
##                    shell_vars={'PATH':'${CL.INSTALL_ROOT}\\VC\\bin'},
##                    test_file='cl.exe'
##                    )
##                ]
##            )
##        #print
##        #print "1)",ts.get_shell_env(self.env.Clone(CL_INSTALL_ROOT=r'C:\Program Files (x86)\Microsoft Visual Studio 9.0'))
##        #print "True=",ts.Exists(self.env.Clone(CL_INSTALL_ROOT=r'C:\Program Files (x86)\Microsoft Visual Studio 9.0'))
##        #print "2)",ts.get_shell_env(self.env.Clone(CL_INSTALL_ROOT=r'.\testdata'))
##        #print "True=",ts.Exists(self.env.Clone(CL_INSTALL_ROOT=r'.\testdata'))
##        #print "False=",ts.Exists(self.env.Clone(CL_INSTALL_ROOT=r'C:\MYPATH'))
##        #try:
##        #    print "3)",ts.get_shell_env(self.env.Clone(CL_INSTALL_ROOT=r'C:\MYPATH'))
##        #except:
##        #    pass
##        #print "True=",ts.Exists(self.env.Clone(CL_INSTALL_ROOT=r'.\testdata',CL_SCRIPT=True))
##
##        #print "4)",ts.get_shell_env(self.env.Clone(CL_INSTALL_ROOT=r'.\testdata',CL_SCRIPT=True))
##


