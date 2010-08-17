import sys
win32=sys.platform == 'win32'

import unittest
from parts.version import *
import SCons.Script

class TestVersionRange(unittest.TestCase):

    def setUp(self):
        pass

    def test_versionrange_pattern_1(self):
        v=version_range('1-2.9')
        self.assertTrue('1.8'in v)
        
    def test_versionrange_pattern_2(self):
        v=version_range('1.0-2.*')
        self.assertTrue('2.9'in v)

    def test_versionrange_pattern_3(self):
        v=version_range('1-2.9')
        self.assertFalse('0.8'in v)        
        
    def test_versionrange_pattern_4(self):
        v=version_range('2.2-2.*')
        self.assertFalse('2.1'in v)

    def test_versionrange_pattern_5_fails_till_fixed(self):  # out of range but we must get it to pass
        v=version_range('1-*')
        self.assertTrue('99999999999999999'in v)

    def test_versionrange_pattern_6(self):
        v=version_range('1-*')
        self.assertTrue('9999999999999999'in v) 

    def test_versionrange_pattern_7(self):
        v=version_range('1-2,!1.5')
        self.assertFalse('1.5'in v) 

    def test_versionrange_pattern_8(self):
        v=version_range('1-2,3-4')
        self.assertFalse('2.5'in v) 

    def test_versionrange_pattern_9(self): 
        v=version_range('1-2,3-4')
        self.assertFalse('4.0.0'in v) 

    def test_versionrange_pattern_10(self):
        v=version_range('1-2,3-4')
        self.assertFalse('4.0.1'in v) 
        
    def test_versionrange_pattern_11(self):
        v=version_range('1.*.4')
        self.assertTrue('1.10.4'in v)

    def test_versionrange_pattern_12(self):
        v=version_range('*-4')
        self.assertTrue('0' in v)

    def test_versionrange_pattern_13(self):
        v=version_range('1.*.4')
        self.assertTrue('1.10.4'in v)    

    def test_versionrange_pattern_14(self): #Crashes with Error
        v=version_range('!2.0')
        self.assertTrue('3.0'in v)        

    def test_versionrange_pattern_15_fails_till_fixed(self): #Fails
        v=version_range(',!2.0')
        self.assertTrue('3.0'in v)        

    def test_versionrange_pattern_16(self): #Crashes with Error
        v=version_range('')
        self.assertTrue('3.0'in v)
        
    def test_versionrange_pattern_17(self): 
        v=version_range(version(2,3,5))
        self.assertTrue('2.3.5'in v)

    def test_versionrange_pattern_18(self):
        v=version_range('')
        self.assertTrue('3.0'in v)    

        