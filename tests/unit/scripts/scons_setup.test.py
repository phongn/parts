import os
import sys

import unittest
from scripts.scons_setup import *

class Test_scons_setup(unittest.TestCase):
    def setUp(self):
        pass

    def test_getSupportedVersions(self):
        '''Test that scons 2.1 is among existing ones'''
        supportedVers = getSupportedVersions()
        self.assertTrue('2.1.0' in supportedVers)

    def test_setupDefault(self):
        '''Test that path to the scons with the highest version is successfully added to python path'''
        # NB: We cannot here a case when scons location is not added to path and scons_setup does this.
        # This is beucase all UTs including this one are invoked via "scons" command therefore scons
        # and Parts are already in path.
        setupDefault()
        self.assertTrue(any(item.lower().find('scons') != -1 for item in sys.path))

        import SCons.Script
        import parts.pnode.section_info as parts_pnode_section_info
