'''
version and version_range implementation to make life easier when dealing with
version strings.
'''
import re, string

__all__ = [
    'version',
    'version_range',
]

class VersionPart:
    '''
    Gives a part of a version number a way to store the string value and a
    weight associated with that string.
    '''
    __slots__ = ["ver", "alwaysMatch", "weight"]
    
    _matchSet = ['*', 'x', 'X']
    
    def __init__(self, strVer, weight = None):
        '''
        Initialize the part and do a little bit of parsing to decern if this is
        a match part.
        '''
        self.ver = strVer
        self.alwaysMatch = strVer in self._matchSet
        self.weight = weight
        
    def compare(self, rhs, comp):
        '''
        Here is where the actual comparison is performed.  If either part has a
        weight, that weight is used in place of the version.  In any other case,
        version is used directly.  'comp' is used as the comparison operator.
        '''
        num1 = self.ver
        if self.weight != None:
            num1 = self.weight
        
        try:
            num2 = rhs.ver
            if rhs.weight != None:
                num2 = rhs.weight
        except AttributeError:
            num2 = rhs
            
        return comp(num1, num2)
    
    def __eq__(self, rhs):
        '''
        Check for equivalence.
        '''
        return self.compare(rhs, lambda x, y: x == y)
    
    def __ne__(self, rhs):
        '''
        Check for not-equal.
        '''
        return self.compare(rhs, lambda x, y: x != y)
    
    def __lt__(self, rhs):
        '''
        Check for less than.
        '''
        return self.compare(rhs, lambda x, y: x < y)
    
    def __le__(self, rhs):
        '''
        Check for less or equal.
        '''
        return self.compare(rhs, lambda x, y: x <= y)
    
    def __gt__(self, rhs):
        '''
        Check for greater than.
        '''
        return self.compare(rhs, lambda x, y: x > y)
    
    def __ge__(self, rhs):
        '''
        Check for greater or equal.
        '''
        return self.compare(rhs, lambda x, y: x >= y)
    
    def __str__(self):
        '''
        Print the string form which just returns the passed in version string.
        '''
        return "%s" % self.ver
        
class version:
    '''
    version object for comparing version numbers.  This also enables special 
    strings to be interpreted with special weight values that can be added or
    removed from the version.weights dictionary.
    '''
    weights = {
        'dev': -1100,
        'alpha': -1000,
        'beta': -900,
        'rc': -800,
        'rtm': -700,
    }
    
    __slots__ = ["ver", "parts", "matches"]
    
    __re = re.compile("(\d*)(\D*)(.*)")
    
    def __init__(self, ver = None, *args):
        '''
        Setup a new version object by copying over from another version, passing
        in a series of items that can be converted to strings, or nothing.  If
        the string version is None or empty, the version number will be treated
        as '0.0.0'.
        '''
        if isinstance(ver, version):
            self.ver = ver.ver
            self.parts = ver.parts[:]
            return;
            
        self.ver = ver
        self.parts = []
        if self.ver:
            self.ver = str(ver)
            for a in args:
                self.ver += ".%s" % str(a)
                
            self._parseVersion()
        else:
            # empty version strings map to '0.0.0'
            self.parts.extend([0, 0, 0])
        
    def _parseVersion(self):
        '''
        Do the initial split on dots and either get the integer form or parse
        the sub piece for a list of version information.
        '''
        for sub in self.ver.split('.'):
            try:
                self.parts.append(int(sub))
            except ValueError:
                ret = self._parseSub(sub);
                if len(ret) == 1:
                    self.parts.extend(ret)
                else:
                    self.parts.append(tuple(ret))
    
    def _parseSub(self, sub):
        '''
        Pull out a list of version parts and integers based on a sub-part of the
        version string.
        '''
        m = self.__re.match(sub)
        if not m:
            # this shouldn't happen, but to be safe
            raise ValueError()
        
        ret = []
        if m.group(1):
            # first group is always an int
            ret.append(int(m.group(1)))
        
        if m.group(2):
            # second will be a possible special string
            part = VersionPart(m.group(2))
            if self.weights.has_key(m.group(2)):
                part.weight = self.weights[m.group(2)]
                
            ret.append(part)
            
        if m.group(3):
            # we recurse to try and decipher the rest
            ret.extend(self._parseSub(m.group(3)))
            
        return ret
        
    def _alwaysMatch(self, p1, p2):
        '''
        Pythonic way of checking if either part has the always match flag set.
        This essentially just checks the alwaysMatch flag and returns True if
        either is True.
        '''
        try:
            if p1.alwaysMatch:
                return True
        except AttributeError:
            pass
        
        try:
            if p2.alwaysMatch:
                return True
        except AttributeError:
            pass
        
        return False
        
    def _compareArray(self, arr1, arr2):
        '''
        Compares two lists and recursively dives into sub-lists.  If there is
        ever a match, this will set the matches variable to True and break out.
        This will always return either the first difference between the arrays
        or their last elements.  This fixes a problem with regular list 
        comparison and the special weight values.
        '''
        len1 = len(arr1)
        len2 = len(arr2)
        if len1 == 0 or len2 == 0:
            self.matches = True
            return len1, len2
            
        for i in range(max(len1, len2)):
            # set default as zero in case one list is longer
            num1 = 0
            num2 = 0
            if i < len1:
                num1 = arr1[i]
                
            if i < len2:
                num2 = arr2[i]
                
            # handle special matches
            if self._alwaysMatch(num1, num2):
                self.matches = True
                break
            
            list1 = isinstance(num1, tuple)
            list2 = isinstance(num2, tuple)
            if list1 or list2:
                # if one is a list, make sure the other is too and recurse
                if not list1:
                    num1 = [num1]
                    
                if not list2:
                    num2 = [num2]
                    
                num1, num2 = self._compareArray(num1, num2)
            
            # first difference makes us stop
            if num1 != num2:
                break
                
        return (num1, num2)
        
    def compare(self, rhs, comp):
        '''
        Central compare function that compares the internal parts arrays.  The
        comp function is used to compare the first differnce in the two lists
        unless there was a match.
        '''
        if not isinstance(rhs, version):
            rhs = version(rhs)
            
        self.matches = False
        num1, num2 = self._compareArray(self.parts, rhs.parts)
        
        return self.matches or comp(num1, num2)
    
    def __eq__(self, rhs):
        '''
        Checks for equivalence.
        '''
        return self.compare(rhs, lambda x, y: x == y)
    
    def __ne__(self, rhs):
        '''
        Checks for not equal.
        '''
        return self.compare(rhs, lambda x, y: x != y)
    
    def __lt__(self, rhs):
        '''
        Checks for less than.
        '''
        return self.compare(rhs, lambda x, y: x < y)
    
    def __le__(self, rhs):
        '''
        Checks for less or equal.
        '''
        return self.compare(rhs, lambda x, y: x <= y)
    
    def __gt__(self, rhs):
        '''
        Checks for greater than.
        '''
        return self.compare(rhs, lambda x, y: x > y)
    
    def __ge__(self, rhs):
        '''
        Checks for greater or equal.
        '''
        return self.compare(rhs, lambda x, y: x >= y)
        
    def __sub__(self, rhs):
        '''
        Subtraction operator that produces a version range with this as the
        start.
        '''
        if rhs == None:
            rhs = "*"
            
        ret = version_range()
        ret.start = version(self)
        ret.end = version(rhs)
            
        return ret
        
    def __rsub__(self, lhs):
        '''
        Subtraction operator that produces a version range with this as the
        end.
        '''
        ret = version_range()
        ret.start = version(lhs)
        ret.end = version(self)
            
        return ret
        
    def short_version_string(self, num = 2, start = 0):
        '''
        Returns a shortened version of the version string starting at start and
        containing num number of sub-version parts.
        '''
        if num < 1:
            return ""
        
        ret = "%s" % str(self.parts[start])
            
        # go through each item in the list and append as necessary
        for i in range(start + 1, start + num):
            ret += "."
            if i >= len(self.parts):
                ret += "0"
                continue
            
            v = self.parts[i]
            if isinstance(v, tuple):
                # we need to iterate through tuples
                for sv in v:
                    ret += str(sv)
            else:
                ret += "%s" % str(v)
               
        return ret
        
    def Major(self):
        return self.short_version_string(1)
        
    def major(self):
        '''
        Compatibility function that effectively returns the first version
        number.
        '''
        return int(self.short_version_string(1))
        
    def Minor(self):
        return self.short_version_string(1, 1)
        
    def minor(self):
        '''
        Compatibility function that effectively returns the second version
        number.
        '''
        return int(self.short_version_string(1, 1))
        
    def Revision(self):
        return self.short_version_string(1, 2)
        
    def revision(self):
        '''
        Compatibility function that effectively returns the third version
        number.
        '''
        return int(self.short_version_string(1, 2))
    
    def __str__(self):
        '''
        Prints the string version.  It basically returns the passed in string.
        '''
        return str(self.ver)

class version_range:
    '''
    Specifies either a start and end value or a set of version ranges to include
    or exclude.  This can then be used with versions to check if they are in a
    particular range.
    '''
    def __init__(self, range = None):
        '''
        Initialize the internal include and exclude arrays and parse the given 
        range.
        '''
        self.range = range
        self.incRight = False
        self.incLeft = True
        self.exclude = False
        self.hasInclude = False
        self.start = self.end = None
        self.ranges = []
        if range:
            if isinstance(range, version):
                self.start = range
            else:
                # remove any whitespace so that the range can be given more
                # naturally
                self.range = range.translate(string.maketrans("", ""), string.whitespace)
                self._parseRanges(self.range)
        
    def _parseRanges(self, range):
        '''
        Splits up the range based on ',' and adds each to the list of ranges.
        '''
        ranges = range.split(',')
        if len(ranges) == 1:
            self._parseRange(range)
            return
            
        for r in ranges:
            if not r:
                # ignore empty ranges
                continue
            
            range = version_range(r)
            if not range.exclude:
                self.hasInclude = True
                
            self.ranges.append(range)
            
    def _parseRange(self, range):
        '''
        Parses a range detecting '[' or ']' and '(' or ')' for inclusive and
        exclusive ranges respectively.  It splits on the '-' and assumes that
        the caller supplied them in the proper order.  A check is also done for
        '!' either inside or outside of the opening '(' or '[' to mark the range
        as an exclude range.
        '''
        if not range:
            return
            
        # check for exclude relationship
        self.exclude = False
        if range[0] == '!':
            self.exclude = True
            range = range[1:]
            
        # check inclusiveness of range
        # these two checks are highly coupled with their default value
        if range[0] == '(':
            self.incLeft = False
        
        if range[-1] == ']':
            self.incRight = True
        
        # trim off the extra notation
        if range[0] in ('(', '['):
            range = range[1:]
        if range[-1] in (')', ']'):
            range = range[:-1]
            
        # check for exclude again in case they stick it inside the brackets
        if range[0] == '!':
            self.exclude = True
            range = range[1:]
        
        # split up the range and create the start and end versions
        splits = range.split('-')
        if len(splits) == 1:
            self.start = version(splits[0])
            return
            
        self.start = version(splits[0])
        self.end = version(splits[1])
            
    def __contains__(self, item):
        '''
        Checks if an item is contained in this range.  The assumption is that
        item is a version object or can be converted to one.  If the range does
        not have an include or exclude list, we only check start and end.  If
        it does have either list, we make sure that at least one range in the
        include list has the item and that none of the excludes have the item.
        If there are no includes, but there are excludes, we assume anything not
        in the excludes is alright.
        '''
        if not isinstance(item, version):
            item = version(item)
            
        # if we don't have includes or excludes, just check start and end
        if len(self.ranges) == 0:
            good = True
            if not self.start:
                pass
            elif not self.end:
                good = self.start == item
            else:
                if self.incLeft:
                    good = item >= self.start
                else:
                    good = item > self.start
                
                if self.incRight:
                    good = good and item <= self.end
                else:
                    good = good and item < self.end
                
            # being excluded means anything in the range is bad
            if self.exclude:
                return not good
            else:
                return good
        
        # check the includes
        excluded = False
        included = False
        for r in self.ranges:
            if item in r:
                if r.exclude:
                    if not self.hasInclude:
                        included = True
                else:
                    included = True
            else:
                # not being in an exclude range means that they were in the
                # underlying range, so they must be excluded
                if r.exclude:
                    excluded = True
                    break
               
        # if there were includes, then it must have been included in one of them
        # we aren't in the range if any range excluded it
        return (not self.hasInclude or included) and not excluded
        
    def bestVersion(self, list):
        '''
        Finds the best version that is in this range from a list of versions.
        The "best" version is defined as the highest version number in the list.
        '''
        for v in reversed(sorted(list)):
            if v in self:
                return version(v)
                
        return None
        
    def __str__(self):
        '''
        Returns the string version of the range.  This is just the passed in
        range string from construction.
        '''
        return str(self.range)
        
if __name__ != '__main__':
    from SCons.Script.SConscript import SConsEnvironment
    
    SConsEnvironment.Version = version
    SConsEnvironment.VersionRange = version_range

########################################
# Everything below here is just test code
########################################
ver = [
    version('1'),              # 0
    version('1.0'),            # 1
    version('2.0'),            # 2
    version('1.1.11'),         # 3
    version('1.1.11beta'),     # 4
    version('1.1.11alpha'),    # 5
    version('1.0a'),           # 6
    version('1.0b'),           # 7
    version('1.1.11beta1rc5'), # 8
    version('1.1.11beta1'),    # 9
    version('2.8'),            # 10
    version('2.2'),            # 11
    version('2.2.1'),          # 12
    version('2.2beta'),        # 13
    version('1.5'),            # 14
    version('1.5.6'),          # 15
    version('1.10'),           # 16
    version('3.0'),            # 17
    version('5.6.7'),          # 18
    version('3.6.3'),          # 19
    version('12.0.6514.5000'), # 20
    version('12.0.6535.5002'), # 21
    version('8.0.7600.16385'), # 22
    version('9.0.30729.1'),    # 23
    version(None),             # 24
    version(''),               # 25
    version(1.2, 3.4, 'beta')  # 26
]
    
ranges = [
    version_range('1.0'),                    # 0
    version_range('1.0-2.0'),                # 1
    version_range('(1.0-2.0]'),              # 2
    version_range('[1.0-2.0)'),              # 3
    version_range('1.0-2.0, 2.2-3'),         # 4
    version_range('1.0-2.0, 2.2-3, !2.8'),   # 5
    version_range('1.0-2, 2.2-3, !2.7-2.9'), # 6
    version_range('1-3, !(2.2-2.9]'),        # 7
    version_range('1.*, !1.5.*'),            # 8
    version_range('1.1*'),                   # 9
    version_range('1.1.11*'),                # 10
    version_range('*'),                      # 11
    version_range('1-2.*'),                  # 12
    version_range('[1-2.*)'),                # 13
    version_range("[1\t-\t\t2\n.*   )"),     # 14
    version_range(ver[19]),                  # 15
    version_range(),                         # 16
    version_range('2.5.2-2.*.*'),            # 17
]

eq = 0
ne = 1
lt = 2
le = 3
gt = 4
ge = 5
contains = 6
notin = 7
    
comp = [
    (lambda x, y: x == y, '=='),
    (lambda x, y: x != y, '!='),
    (lambda x, y: x < y, '< '),
    (lambda x, y: x <= y, '<='),
    (lambda x, y: x > y, '> '),
    (lambda x, y: x >= y, '>='),
    (lambda x, y: x in y, '    in'),
    (lambda x, y: x not in y, 'not in'),
]
        
def testSummary(passed, failed, failures = None):
    '''
    Print a summary of pass/failure information.
    '''
    total = passed + failed
    print '*' * 40
    print '* Test Summary'
    if failed > 0:
        print '* %d test(s) failed!' % failed
        if failures:
            print '* %s' % failures
        
    print '* %d%% (%d/%d) passed' % (passed * 100 / total, passed, total)
    print '*' * 40

def compTestRun(ver1, ver2, comp, expected):
    '''
    Run and print the result of comparing ver1 and ver2 and seeing if the result
    matches expected.
    '''
    result = comp[0](ver1, ver2)
    outResult = 'PASSED'
    if result != expected:
        outResult = 'FAILED'
        
    print "[%s] %s %s %s is %s" % (outResult, ver1, comp[1], ver2, result)
    
    return result == expected
    
def doTests(testCases, arr1, arr2):
    '''
    Run through a set of test cases whose inputs are pulled from arr1 and arr2.
    '''
    failed = 0
    passed = 0
    cur = 0
    total = temp = len(testCases)
    mult = 1
    failures = []
    temp /= 10
    while temp:
        mult += 1
        temp /= 10
        
    for t in testCases:
        cur += 1
        print "%*d." % (mult, cur),
        if compTestRun(arr1[t[0]], arr2[t[1]], comp[t[2]], t[3]):
            passed += 1
        else:
            failed += 1
            failures.append(cur)
          
    testSummary(passed, failed, failures)
    
    return passed, failed
    
def testStart(header):
    print
    print '=' * 40
    print '= %s' % header
    print '=' * 40

def compTest():
    '''
    Run through a bunch of different comparison checks.
    '''
    testStart('Comparison Tests')
    
    testCases = [
        # ver1, ver2, operation, expected
        (0, 0, eq, True),
        (0, 0, ne, False),
        (0, 0, lt, False),
        (0, 0, le, True),
        (0, 0, gt, False),
        (0, 0, ge, True),
        
        (0, 1, eq, True),
        (0, 1, ne, False),
        (0, 1, lt, False),
        (0, 1, le, True),
        (0, 1, gt, False),
        (0, 1, ge, True),
        
        (0, 2, eq, False),
        (0, 2, ne, True),
        (0, 2, lt, True),
        (0, 2, le, True),
        (0, 2, gt, False),
        (0, 2, ge, False),
        
        (2, 1, eq, False),
        (2, 1, ne, True),
        (2, 1, lt, False),
        (2, 1, le, False),
        (2, 1, gt, True),
        (2, 1, ge, True),
        
        (3, 2, eq, False),
        (3, 2, ne, True),
        (3, 2, lt, True),
        (3, 2, le, True),
        (3, 2, gt, False),
        (3, 2, ge, False),
        
        # ver1, ver2, operation, expected
        (3, 4, eq, False),
        (3, 4, ne, True),
        (3, 4, lt, False),
        (3, 4, le, False),
        (3, 4, gt, True),
        (3, 4, ge, True),
        
        (5, 4, eq, False),
        (5, 4, ne, True),
        (5, 4, lt, True),
        (5, 4, le, True),
        (5, 4, gt, False),
        (5, 4, ge, False),
        
        (0, 6, eq, False),
        (0, 6, ne, True),
        (0, 6, lt, True),
        (0, 6, le, True),
        (0, 6, gt, False),
        (0, 6, ge, False),
        
        (7, 6, eq, False),
        (7, 6, ne, True),
        (7, 6, lt, False),
        (7, 6, le, False),
        (7, 6, gt, True),
        (7, 6, ge, True),
        
        (8, 4, eq, False),
        (8, 4, ne, True),
        (8, 4, lt, False),
        (8, 4, le, False),
        (8, 4, gt, True),
        (8, 4, ge, True),
        
        # ver1, ver2, operation, expected
        (8, 9, eq, False),
        (8, 9, ne, True),
        (8, 9, lt, True),
        (8, 9, le, True),
        (8, 9, gt, False),
        (8, 9, ge, False),
        
        (24, 22, eq, False),
        (22, 25, eq, False),
    ]
    
    return doTests(testCases, ver, ver)
    
def rangeTest():
    '''
    Go through various checks involving versions and ranges.
    '''
    testStart('Range Tests')
    
    testCases = [
        # ver, range, comp, expected
        (0, 0, contains, True),
        (0, 0, notin, False),
        
        (2, 0, contains, False),
        (2, 0, notin, True),
        
        (0, 1, contains, True),
        (0, 1, notin, False),
        
        (8, 1, contains, True),
        (8, 1, notin, False),
        
        (2, 1, contains, False),
        (2, 1, notin, True),
        
        (0, 2, contains, False),
        (0, 2, notin, True),
        
        (2, 2, contains, True),
        (2, 2, notin, False),
        
        (0, 3, contains, True),
        (0, 3, notin, False),
        
        (2, 3, contains, False),
        (2, 3, notin, True),
        
        (10, 4, contains, True),
        (10, 4, notin, False),
        
        (10, 5, contains, False),
        (10, 5, notin, True),
        
        (10, 6, contains, False),
        (10, 6, notin, True),
        
        (11, 7, contains, True),
        (11, 7, notin, False),
        
        # ver, range, comp, expected
        (12, 7, contains, False),
        (12, 7, notin, True),
        
        (13, 7, contains, True),
        (13, 7, notin, False),
        
        (3, 8, contains, True),
        (3, 8, notin, False),
        
        (14, 8, contains, False),
        (14, 8, notin, True),
        
        (15, 8, contains, False),
        (15, 8, notin, True),
        
        (3, 9, contains, True),
        (3, 9, notin, False),
        
        (16, 9, contains, False),
        (16, 9, notin, True),
        
        (3, 10, contains, True),
        (3, 10, notin, False),
        
        (8, 10, contains, True),
        (8, 10, notin, False),
        
        (8, 11, contains, True),
        (8, 11, notin, False),
        
        (5, 11, contains, True),
        (5, 11, notin, False),
        
        (3, 11, contains, True),
        (3, 11, notin, False),
        
        (10, 12, contains, True),
        (10, 12, notin, False),
        
        # ver, range, comp, expected
        (17, 12, contains, False),
        (17, 12, notin, True),
        
        (10, 13, contains, True),
        (10, 13, notin, False),
        
        (17, 13, contains, False),
        (17, 13, notin, True),
        
        (10, 14, contains, True),
        (10, 14, notin, False),
        
        (17, 14, contains, False),
        (17, 14, notin, True),
        
        (19, 15, contains, True),
        (19, 15, notin, False),
        
        (18, 15, contains, False),
        (18, 15, notin, True),
        
        (18, 16, contains, True),
        (18, 16, notin, False),
        
        (10, 17, contains, True),
        (10, 17, notin, False),
    ]
    
    return doTests(testCases, ver, ranges)
    
def customWeightsTest():
    '''
    Do some comparisons using custom weights.
    '''
    testStart('Custom Weight Tests')
    
    weights = {
        'a': 4,
        'b': 3,
        'c': 2,
        'd': 1,
        'git': version.weights['dev'],
    }
    
    version.weights.update(weights)
    localVer = [
        version('a.a'),
        version('a.b'),
        version('a.b.git'),
        version('a.b.dev'),
    ]
    
    testCases = [
        (0, 0, eq, True),
        (1, 0, eq, False),
        (1, 0, lt, True),
        (2, 1, lt, True),
        (2, 3, eq, True),
    ]
    
    return doTests(testCases, localVer, localVer)
    
def shortTest():
    testStart('Short version Tests')
    
    expectedShortVer = [
        '1.0',
        '1.0',
        '2.0',
        '1.1',
        '1.1',
        '1.1',
        '1.0a',
        '1.0b',
        '1.1',
        '1.1',
        '2.8',
        '2.2',
        '2.2',
        '2.2beta',
        '1.5',
        '1.5',
        '1.10',
        '3.0',
        '5.6',
        '3.6',
        '12.0',
        '12.0',
        '8.0',
        '9.0',
        '0.0',
        '0.0',
        '1.2',
    ]
    
    shortVer = []
    testCases = []
    for i,v in enumerate(ver):
        shortVer.append(v.short_version_string())
        testCases.append((i, i, eq, True))
    
    return doTests(testCases, shortVer, expectedShortVer)
   
def stringTest():
    '''
    Different tests to validate string comparison with Versions.
    '''
    testStart('String Comparison Tests')
    
    strList = [
        '5.6.7',
        '12.0.6514.5000',
        None,
    ]
    
    testCases = [
        # strList, ver, comp, expected
        (0, 18, eq, True),
        (1, 18, eq, False),
        (2, 24, eq, True),
    ]
    
    return doTests(testCases, strList, ver)
    
def bestTest():
    testStart('Best of Tests')
    
    best = []
    
    bestExp = [
        '2.0',
        None,
    ]
    
    list = [ver[8], ver[6], ver[13], ver[2], ver[9]]
    best.append(ranges[2].bestVersion(list))
    best.append(ranges[17].bestVersion(list))
    
    testCases = [
        # best, bestExp, comp, expected
        (0, 0, eq, True),
        (1, 1, eq, True),
    ]
    
    return doTests(testCases, bestExp, best)
    
def tests():
    '''
    Run through the set of tests.
    '''
    total = [0, 0] # pass, fail
    
    total = [sum(pair) for pair in zip(total, compTest())]
    total = [sum(pair) for pair in zip(total, rangeTest())]
    total = [sum(pair) for pair in zip(total, customWeightsTest())]
    total = [sum(pair) for pair in zip(total, shortTest())]
    total = [sum(pair) for pair in zip(total, stringTest())]
    total = [sum(pair) for pair in zip(total, bestTest())]
    
    print
    testSummary(total[0], total[1])
        
# this is just a bunch of test cases
if __name__ == '__main__':
    tests()
