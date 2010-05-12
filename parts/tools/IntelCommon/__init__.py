
from common import Intelc
import sys
#if windows
if sys.platform=='win32':
    import intelc_win32,intelc_win32_91,intelc_win32_12
else:
    #if posix
    import intelc_posix
