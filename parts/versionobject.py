''' 
This file was written by albert to setup a base version object concept.
He tries some idea with adding the version and tool together. Might be worth
expploring latter. But at this time it seem not as useful as first thought'''


import string

#---------------------------------------------------------------------
# Constants
#---------------------------------------------------------------------

# Error messages

ERRMSG_PRODUCT_PREFIX_MISMATCH = \
	"Error: Version string '%s' must contain product prefix '%s' instead of '%s'."
ERRMSG_TOO_MANY_ARGUMENTS = \
	"Error: Version string '%s' has too many arguments."
ERRMSG_VERSION_NUMBER_NOT_NUMERIC = \
	"Error: Version number string '%s' contains non-numeric characters."

#---------------------------------------------------------------------
# parseVersionNumber
#
# Parses a version number string such as '8.1.0' and returns 
# major_number, minor_number, and revision_number.	For any of these
# fields, a value of -1 means 'any'.  For example, '8.x.1' would return
# 8, -1, and 1.  The given version number string must not start with a 
# product prefix.
#
# Returns (error_msg, major_number, minor_number, revision_number).
# error_msg is an empty string if there is no error.
#---------------------------------------------------------------------
def parseVersionNumber(versionNumber):
	fields = string.split(versionNumber, '.')
	fieldValues = [0, 0, 0] 	# default values

	for i in range(len(fields)):
		if fields[i] == 'x' or fields[i] == 'X' or fields[i] == '*':
			value = -1
		else:
			try:
				value = int(fields[i])
			except ValueError, msg:
				return (ERRMSG_VERSION_NUMBER_NOT_NUMERIC % versionNumber, 0, 0, 0)

		fieldValues[i] = value

		# Parse only as many version numbers as we have room for
		if i + 1 == len(fieldValues):
			break

	return ('', fieldValues[0], fieldValues[1], fieldValues[2])

#---------------------------------------------------------------------
# CompareVersionNumbers
#
# Compares two discrete version numbers and returns (error_msg, result) 
# where error_msg is an emptry string if there is no error.  
# result contains the result of the comparison
# as follows:
#
#	result = 0: versionNumber1 = versionNumber2
#	result < 0: versionNumber1 < versionNumber2
#	result > 0: versionNumber1 > versionNumber2
#
# Arguments must be in the discrete version string format, e.g. '8.1.2'.
# Argument of None is considered to be '0.0.0'.
#
# Returns (error_message, result) where error_message is '' if no error.
#---------------------------------------------------------------------
def CompareVersionNumbers(verStr1, verStr2):
	if verStr1 == None and verStr2 == None:
		return ('', 0)

	if verStr1 == None and verStr2 != None:
		return ('', -1)

	if verStr1 != None and verStr2 == None:
		return ('', 1)

	errmsg, major1, minor1, rev1 = parseVersionNumber(verStr1)
	if errmsg != '':
		return (errmsg, 0)

	errmsg, major2, minor2, rev2 = parseVersionNumber(verStr2)
	if errmsg != '':
		return (errmsg, 0)

	if major1 < major2:
		return ('', -1)
	if major1 > major2:
		return ('', 1)
	
	if minor1 < minor2:
		return ('', -1)
	if minor1 > minor2:
		return ('', 1)

	if rev1 < rev2:
		return ('', -1)
	if rev1 > rev2:
		return ('', 1)

	return ('', 0)

#---------------------------------------------------------------------
# UnitTest
#
# Performs a unit test and returns the results.
#---------------------------------------------------------------------
def UnitTest():
	testTable = [
		#
		# (valid versions, test version, expected result)

		('7.1-7.*', '7.0.0', False),
		('7.0.0','7.1-7.*', False),
		('7.1-7.*', '7', False),
		('7','7.1-7.*', False),
		('7.1-7.*', '7.2', True),
		('7.2','7.1-7.*', True),
		('7.*-7.1', '7.2', False),
		('7.2','7.*-7.1', False),

		('cygwin16', 'cygwin16', True),
		('cygwin16', 'cygwin32', False),
		('cygwin16, cygwin32', 'cygwin16', True),
		('cygwin16, cygwin32', 'cygwin32', True),
		('cygwin16, cygwin32', 'cygwin64', False),
		('cygwin16-cygwin32', 'cygwin16', True),
		('cygwin16-cygwin32', 'cygwin64', False),

		('cl_8.0', 'cl_8.0', True),
		('cl_8.0', 'cl_8.1', False),
		('cl_8.0, cl_9.0', 'cl_8.0.1', False),
		('cl_8.0, cl_9.0', 'cl_9.0', True),
		('cl_8.0, cl_9.0', 'cl_7.0', False),
		('cl_8.0, cl_9.1.1', 'cl_9.1.2', False),
		('cl_8.0-cl_9.0', 'cl_8.2', True),
		('cl_8.0-cl_9.0', 'cl_7.9', False),
		('cl_8.0-cl_9.0', 'cl_9.1', False),
		('cl_8.x', 'cl_8.0.5', True),
		('cl_8.x', 'cl_8.5.0', True),
		('cl_8.*', 'cl_8.0.5', True),
		('cl_8.*', 'cl_8.5.0', True),
		('cl_8.*', 'cl_9.5.0', False),
		('cl_8.1.*', 'cl_8.0.0', False),
		('cl_8.1.*', 'cl_8.5.0', False),
		('cl_8.1.*', 'cl_8.0', False),
		('cl_8.1.*', 'cl_8.5', False),
		('8.1-*', '8.0', False),
		('8.0','8.1-*', False),
		('cl_8.0-cl_9.0, !cl_8.2', 'cl_8.1', True),
		('cl_8.0-cl_9.0, !cl_8.2', 'cl_8.2', False),
		('cl_8.0-cl_9.0, !cl_8.2', 'cl_8.2.1', True),
		('cl_8.0, cl_9.0-cl_10.0, !cl_9.5-cl_9.6', 'cl_8.0', True),
		('cl_8.0, cl_9.0-cl_10.0, !cl_9.5-cl_9.6', 'cl_9.4', True),
		('cl_8.0, cl_9.0-cl_10.0, !cl_9.5-cl_9.6', 'cl_9.5.5', False),
		('cl_8.0, cl_9.0-cl_10.0, !cl_9.5-cl_9.6', 'cl_9.6.1', True),
	]

	allPassed = True

	print "Performaing unit test..."

	index = 1
	for entry in testTable[:]:
		str1, str2, expectedResult = entry
		v1 = VersionObject(str1)
		v2 = VersionObject(str2)

		if expectedResult != v1.Match(v2):
			allPassed = False
			print "Unit test FAILED on trying to match '%s' with '%s'." % (str1, str2)
			break

		index += 1

	if allPassed:
		print "Unit test passed."
	else:
		print "Unit test %d %s FAILED." % (index, testTable[index - 1])

#-------------------------------------------------------------------------
# VersionObject
#
# An object that allows for version specifiers to be compared.	The version
# specifier may or may not contain the version number.	If both the product
# specifier and the version number are present, they must be separated by
# an underscore character.
#
# NOTE:
# 1. All specifiers are CASE-SENSITIVE.
# 2. Specifier 'x', such as in 8.x, must not occur in ranges.
#
# Examples:
#
#	'cygwin'					- Any and all versions of cygwin
#	'prof_c++, enterprise_c++'	- prof_c++ or enterprise_c++
#	'cl_8.0'					- Version 8.0
#	'cl_8.0, cl_9.0'			- 8.0 and 9.0
#	'cl_8.0-cl_9.0' 			- 8.0 through 9.0
#	'cl_8.x'					- 8.x, minor version does not matter
#	'cl_8.*'					- Same as 8.x
#	'cl_8.0-cl_9.0, !cl_8.2-cl8.3'	 - 8.0 through 9.0 EXCEPT 8.2-8.3
#	'cl_8.0-cl_9.0, cl_11.0-cl_12.0' - 8.0 through 9.0, 11.0 through 12.0
#	'8.0'				 - Version 8.0
#	'8.0, 9.0'			 - 8.0 and 9.0
#	'8.0-9.0'			 - 8.0 through 9.0
#	'8.x'				 - 8.x, minor version does not matter
#	'8.0-9.0, !8.2-8.3'  - 8.0 through 9.0 EXCEPT 8.2-8.3
#	'8.0-9.0, 11.0-12.0' - 8.0 through 9.0, 11.0 through 12.0
#-------------------------------------------------------------------------
class VersionObject:

	#---------------------------------------------------------------------
	# _init_
	#
	# Constructor.
	#---------------------------------------------------------------------
	def __init__(self, versionStr=None, productName=None):
		self.productName = productName	# product name
		self.versionStr = versionStr	# saved version string
		self.productPrefix = None		# product prefix
		self.validRanges = []			# tuples of valid ranges
		self.invalidRanges = [] 		# tuples of invalid ranges
		self.lastMatchError = ''		# error string from last match

		# Parse the constructor argument.

		if versionStr != None:
			result = self.Parse(versionStr)
			if result != '':
				print result

	#---------------------------------------------------------------------
	# Match
	#
	# Tries to match the specified version string such as '7.0', 'cl_8.0',
	# or 'ms_standard' to the object's version specification to see 
	# if there is a match.
	#
	# The versionStr argument can be either a version string or a version
	# object.
	#
	# Returns True if the versions match.
	#---------------------------------------------------------------------
	def Match(self, str):
		if isinstance(str, VersionObject):
			# Check both ways in case arguments are swapped.  If either
			# matches, then there is a match.
			result1 = self.MatchSub(str)
			result2 = str.MatchSub(self)
			return (result1 or result2)

		return self.MatchSub(str);
	
	def MatchSub(self, str):
		self.lastMatchError = ''
		if str == None:
			return False

		if isinstance(str, VersionObject):
			versionStr = str.validRanges[0][0]
		else:
			versionStr = str

		versionStr = string.lower(versionStr)

		# Perform a quick check for an exact match first

		for validRange in self.validRanges[:]:
			if versionStr in validRange:
				return True

		# Instantiate a VersionObject with the version string argument

		if isinstance(str, VersionObject):
			obj = str
		else:
			obj = VersionObject(versionStr)
	
		matchFound = False

		for validRange in self.validRanges[:]:
			if self.checkRange(obj, validRange):
				matchFound = True
				break

		if not matchFound:
			return False

		# Check the invalid ranges to make sure the version doesn't fall there

		for invalidRange in self.invalidRanges[:]:
			if self.checkRange(obj, invalidRange):
				return False

		return matchFound

	#---------------------------------------------------------------------
	# Clear
	#
	# Clears the object's version info.
	#---------------------------------------------------------------------
	def Clear(self):
		self.productPrefix = None
		self.validRanges = []
		self.invalidRanges = []

	#---------------------------------------------------------------------
	# Parse
	#
	# Parses the given version string according to the rules laid out
	# in the class description, and fills out the member variables.
	#
	# Returns an empty string if the parsing was successful.
	#---------------------------------------------------------------------
	def Parse(self, versionStr):

		self.validRanges = []
		self.invalidRanges = []
		self.versionStr = versionStr

		if versionStr == None:
			return ''	# nothing to do
		
		versionStr = string.strip(versionStr)
		if versionStr == '':
			return ''
		
		# Separate out multiple ranges delimited by ','.

		ranges = string.split(versionStr, ',')
		
		for rangeItem in ranges[:]:
			minVersion = None		# minimum version in the range
			maxVersion = None		# maximum version in the range
			excludeRange = False	# True if these are excluded versions

			rangeItem = string.strip(rangeItem) # ignore whitespaces
			
			# If the version string starts with a '!' then these are excluded versions.

			if len(rangeItem) and rangeItem[0] == '!':
				rangeItem = rangeItem[1:]
				excludeRange = True

			# Separate out minimum and maximum range delimited by '-'.

			fields = string.split(rangeItem, '-')

			if len(fields) > 2:
				return ERRMSG_TOO_MANY_ARGUMENTS % versionStr
			
			for fieldItem in fields[:]:
				fieldItem = string.strip(fieldItem) # ignore whitespaces

				chIndex = -1			# current character position
				productPrefix = ''		# product prefix
				productVersion = fieldItem	# product version - assume default value

				# Search backwards to find the product prefix and the product version.

				for i in range(len(fieldItem)):
					ch = fieldItem[chIndex]
					if ch == '_':
						productPrefix = fieldItem[:chIndex]
						productVersion = fieldItem[chIndex + 1:]
						break
					chIndex -= 1

				if self.productPrefix == None:
					self.productPrefix = productPrefix
				else:
					if self.productPrefix != productPrefix:
						return ERRMSG_PRODUCT_PREFIX_MISMATCH % \
							(versionStr, self.productPrefix, productPrefix)

				# Save the version value.

				if minVersion == None:
					minVersion = productVersion
				else:
					maxVersion = productVersion

			# Save off the versions.

			if maxVersion == None:
				maxVersion = minVersion

			minVersion = string.replace(minVersion, "*", "0")
			maxVersion = string.replace(maxVersion, "*", "999999999")
			minVersion = string.replace(minVersion, "x", "0")
			maxVersion = string.replace(maxVersion, "x", "999999999")
			if excludeRange:
				self.invalidRanges.append((minVersion, maxVersion))
			else:
				self.validRanges.append((minVersion, maxVersion))

		return ''

	#---------------------------------------------------------------------
	# AddValidVersions
	#
	# Adds discrete versions, separated by commas, to the valid range.
	# Note: No verification will be performed on the given string.
	#---------------------------------------------------------------------
	def AddValidVersions(self, versions):
		for version in versions[:]:
			self.validRanges.append((version, version))

	#---------------------------------------------------------------------
	# AddInvalidVersions
	#
	# Adds discrete versions, separated by commas, to the invalid range.
	# Note: No verification will be performed on the given string.
	#---------------------------------------------------------------------
	def AddInvalidVersions(self, versionStr):
		versions = string.split(versionStr, ',')
		for version in versions[:]:
			version = string.strip(version)
			self.invalidRanges.append((version, version))

	#---------------------------------------------------------------------
	# Dump
	#
	# Prints the internal contents of the object as a string.
	#---------------------------------------------------------------------
	def Dump(self):
		ret = "%s\n" % self.validRanges

		# Show invalid ranges only if it is not empty since most objects
		# will not have invalid ranges.

		if len(self.invalidRanges):
			ret += "Invalid ranges:\n%s" % self.invalidRanges

		print ret

	#---------------------------------------------------------------------
	# ListValidVersions
	#
	# Returns the first element from each valid range.	Useful for
	# displaying discrete versions to user.
	#---------------------------------------------------------------------
	def ListValidVersions(self):
		ret = []
		for range in self.validRanges[:]:
			ret.append(range[0])

		return ret

	#---------------------------------------------------------------------
	# ToString
	#
	# Returns the version string that was used to construct this object.
	#---------------------------------------------------------------------
	def ToString(self):
		return self.versionStr

	#---------------------------------------------------------------------
	# checkRange
	#
	# Checks the given version object to see if its version number
	# falls within the given version range.
	#
	# Returns True if the version falls within the specified ranges.
	#---------------------------------------------------------------------
	def checkRange(self, obj, validRange):
		if self.productPrefix != obj.productPrefix:
			return False	# product prefixes must match

		if len(obj.validRanges) == 0 or len(self.validRanges) == 0:
			return False	# there are no valid ranges

		lower, upper = validRange
		nonNumericMatch = False 	# set to True if non-numeric match is required

		self.lastMatchError, lowerMajor, lowerMinor, lowerRev = parseVersionNumber(lower)

		if self.lastMatchError != '':
			nonNumericMatch = True
		else:
			self.lastMatchError, upperMajor, upperMinor, upperRev = parseVersionNumber(upper)
			if self.lastMatchError != '':
				return False	# The upper range string cannot be non-numeric

		objVersionStr = obj.validRanges[0][0]

		self.lastMatchError, objMajor, objMinor, objRev = parseVersionNumber(objVersionStr)
		if self.lastMatchError != '':
			nonNumericMatch = True

		if nonNumericMatch:
			#
			# The version being checked for contains non-numeric characters.  In this case,
			# we can only check for an exact match.

			self.lastMatchError = ''
			return (objVersionStr == lower)

		if lowerMajor == -1 or upperMajor == -1:
			return True 	# any version will do

		if objMajor < lowerMajor or objMajor > upperMajor:
			return False	# version falls outside range

		# Major version is valid.  Check the minor version.

		if lowerMinor == -1 or upperMinor == -1:	# any minor version will do
			return True

		if objMajor == lowerMajor and objMinor < lowerMinor:
			return False	# minor version is too small

		if objMajor == upperMajor and objMinor > upperMinor:
			return False	# minor version is too big

		# Minor version is valid.  Check the revision version.

		if lowerRev == -1 or upperRev == -1:	# any revision version will do
			return True

		if objMajor == lowerMajor and objMinor == lowerMinor and objRev < lowerRev:
			return False	# revision version is too small

		if objMajor == upperMajor and objMinor == upperMinor and objRev > upperRev:
			return False	# revision version is too big

		return True

if __name__ == '__main__':
	UnitTest()
