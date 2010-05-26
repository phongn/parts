
from common import Intelc
import sys
#if windows
if sys.platform=='win32':
    import intelc_win32,intelc_win32_91,intelc_win32_12
else:
    #if posix or mac ( mac may become it owns file latter)
    import intelc_posix
