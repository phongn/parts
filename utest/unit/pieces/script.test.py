import sys
win32=sys.platform == 'win32'

import unittest
from parts.pieces.merge_script import *
import SCons.Script
import sys
is_win32=False
if sys.platform == 'win32':
    is_win32=True

#### tests for Finder objects


class TestMergeScript(unittest.TestCase):

    def setUp(self):
        self.env=SCons.Script.Environment(tools=[])

    if is_win32:
        def test_script_env_win(self):
            r = get_script_env(self.env,'testdata\\testvars.cmd',vars=['INCLUDE'])
            self.assertEqual(len(r),1)
            self.assertEqual( r.get('INCLUDE',None), r'C:\Program Files (x86)\joe\myinclude\INCLUDE;C:\foo\INCLUDE;oddvar;;;like this')

        def test_merge_env_win(self):
            cenv=self.env.Clone()
            merge_script_vars(cenv,'testdata\\testvars.cmd',vars=['INCLUDE'])
            #print cenv.Dump('ENV')
            self.assertEqual( cenv['ENV'].get('INCLUDE',None), r'C:\Program Files (x86)\joe\myinclude\INCLUDE;C:\foo\INCLUDE;oddvar;like this')
        
        