import errno
import sys
import os
import subprocess
import collections

from SCons.Errors import UserError

class ProcessAction:
    SUSPEND =   'suspend'
    TERMINATE = 'terminate'
    RESUME =    'resume'

def _callWithCheck(message, *call_args, **call_kw):
    call_kw['stdout'] = subprocess.PIPE
    call_kw['stderr'] = subprocess.PIPE
    proc = subprocess.Popen(*call_args, **call_kw)
    stdout, stderr = proc.communicate()
    if proc.returncode != 0:
        raise UserError(message.format(proc.returncode, '%s\n\n%s' % (stdout, stderr)))
    return stdout

if os.name == 'nt':
    import ctypes
    from ctypes.wintypes import DWORD, HANDLE, BOOL

    # constants taken from MSDN
    TH32CS_SNAPPROCESS = 0x2    # snapshot all the processes on the system
    TH32CS_SNAPTHREAD = 0x4     # snapshot all the threads on the system
    THREAD_SUSPEND_RESUME = 0x2 # suspend or resume a thread
    PROCESS_TERMINATE = 0x1     # terminate a process

    MAX_PATH = 260

    SmallProcessInfo = collections.namedtuple('SmallProcessInfo', 'name pid ppid')
    SmallThreadInfo = collections.namedtuple('SmallThreadInfo', 'tid pid')

    class ProcessEntry32(ctypes.Structure):
        _fields_ = [('dwSize',              DWORD),
                    ('cntUsage',            DWORD),
                    ('th32ProcessID',       DWORD),
                    ('th32DefaultHeapID',   ctypes.POINTER(ctypes.c_ulong)),
                    ('th32ModuleID',        DWORD),
                    ('cntThreads',          DWORD),
                    ('th32ParentProcessID', DWORD),
                    ('pcPriClassBase',      ctypes.c_long),
                    ('dwFlags',             DWORD),
                    ('szExeFile',           ctypes.c_char * MAX_PATH)]

        def __init__(self):
            ctypes.Structure.__init__(self)
            self.dwSize = ctypes.sizeof(self)

        def getInfo(self):
            return SmallProcessInfo(self.szExeFile, self.th32ProcessID, self.th32ParentProcessID)

    class ThreadEntry32(ctypes.Structure):
        _fields_ = [('dwSize',             DWORD),
                    ('cntUsage',           DWORD),
                    ('th32ThreadID',       DWORD),
                    ('th32OwnerProcessID', DWORD),
                    ('tpBasePri',          ctypes.c_long),
                    ('tpDeltaPri',         ctypes.c_long),
                    ('dwFlags',            DWORD)]

        def __init__(self):
            ctypes.Structure.__init__(self)
            self.dwSize = ctypes.sizeof(self)

        def getInfo(self):
            return SmallThreadInfo(self.th32ThreadID, self.th32OwnerProcessID)

    WaitForSingleObject = ctypes.windll.kernel32.WaitForSingleObject
    WaitForSingleObject.argtypes = (HANDLE, DWORD)

    CloseHandle = ctypes.windll.kernel32.CloseHandle
    CloseHandle.restype = BOOL
    CloseHandle.argtypes = (HANDLE, )

    CreateToolhelp32Snapshot = ctypes.windll.kernel32.CreateToolhelp32Snapshot
    CreateToolhelp32Snapshot.restype = HANDLE
    CreateToolhelp32Snapshot.argtypes = (DWORD, DWORD)

    Process32First = ctypes.windll.kernel32.Process32First
    Process32First.argtypes = (HANDLE, ctypes.POINTER(ProcessEntry32))
    Process32First.restype = BOOL

    Process32Next = ctypes.windll.kernel32.Process32Next
    Process32Next.argtypes = (HANDLE, ctypes.POINTER(ProcessEntry32))
    Process32Next.restype = BOOL

    Thread32First = ctypes.windll.kernel32.Thread32First
    Thread32First.argtypes = (HANDLE, ctypes.POINTER(ThreadEntry32))
    Thread32First.restype = BOOL

    Thread32Next = ctypes.windll.kernel32.Thread32Next
    Thread32Next.argtypes = (HANDLE, ctypes.POINTER(ThreadEntry32))
    Thread32Next.restype = BOOL

    OpenThread = ctypes.windll.kernel32.OpenThread
    OpenThread.argtypes = (DWORD, BOOL, DWORD)
    OpenThread.restype = HANDLE

    SuspendThread = ctypes.windll.kernel32.SuspendThread
    SuspendThread.argtypes = (HANDLE, )
    SuspendThread.restype = DWORD

    OpenProcess = ctypes.windll.kernel32.OpenProcess
    OpenProcess.argtypes = (DWORD, BOOL, DWORD)
    OpenProcess.restype = HANDLE

    TerminateProcess = ctypes.windll.kernel32.TerminateProcess
    TerminateProcess.argtypes = (HANDLE, ctypes.c_uint)
    TerminateProcess.restype = BOOL

    def __waitForProcess(process, timeout):
        # WaitForSingleObject expects timeout in milliseconds, so we convert it
        WaitForSingleObject(int(process._handle), int(timeout * 1000))

    def _traverseWinStructures(snapFlags, entryClass, traverseFirst, traverseNext):
        snapHandle = CreateToolhelp32Snapshot(snapFlags, 0)
        if snapHandle == HANDLE(-1):
            raise ctypes.WinError()
        try:
            entry = entryClass()
            res = traverseFirst(snapHandle, ctypes.pointer(entry))
            if not res:
                raise ctypes.WinError()
            while res:
                yield entry.getInfo()
                res = traverseNext(snapHandle, ctypes.pointer(entry))
        finally:
            CloseHandle(snapHandle)

    def _listAllProcesses():
        for name, pid, ppid in _traverseWinStructures(TH32CS_SNAPPROCESS, ProcessEntry32,
                                            Process32First, Process32Next):
            yield pid, ppid

    def _listAllThreads():
        for entry in _traverseWinStructures(TH32CS_SNAPTHREAD, ThreadEntry32,
                                            Thread32First, Thread32Next):
            yield entry

    def suspendThread(tid):
        threadHandle = OpenThread(THREAD_SUSPEND_RESUME, False, tid)
        if threadHandle == 0:
            raise ctypes.WinError()
        try:
            if SuspendThread(threadHandle) == DWORD(-1):
                raise ctypes.WinError()
        finally:
            CloseHandle(threadHandle)

    def suspendProcess(pid):
        for tid, ownerPid in _listAllThreads():
            if ownerPid == pid:
                suspendThread(tid)

    def terminateProcess(pid):
        procHandle = OpenProcess(PROCESS_TERMINATE, False, pid)
        if procHandle == 0:
            raise ctypes.WinError()
        try:
            if TerminateProcess(procHandle, 128) == 0:
                raise ctypes.WinError()
        finally:
            CloseHandle(procHandle)


    PROCESS_ACTIONS = {ProcessAction.SUSPEND: suspendProcess,
                       ProcessAction.TERMINATE: terminateProcess,
                       ProcessAction.RESUME: lambda pid: None}
    def _performAction(pid, action):
        try:
            PROCESS_ACTIONS[action](pid)
        except BaseException, e:
            raise UserError('Cannot {2} PID {0}: {1}'.format(pid, e, action))

    def killProcessTree(proc):
        # we do this because terminate process get complex with shell involed, also we want to
        # terminate all the process tree
        _callWithCheck('Cannot kill PID %s: TASKKILL rc = {0}, output = {1}' % proc.pid,
                       "TASKKILL /F /T /PID {0}".format(proc.pid), shell=True)

elif os.name == 'posix':
    import signal
    import time
    import re

    if sys.platform in ('linux2', 'cygwin'):
        if signal.getsignal(signal.SIGCHLD) in (signal.SIG_DFL, signal.SIG_IGN):
            # We need to install an empty signal handler, otherwise SIGCHLD would be ignored
            # and time.sleep() won't be interrupted when a child dies. We also need to do so in
            # main thread (see "signal" module documentation).
            signal.signal(signal.SIGCHLD, lambda *args: None)
            signal.siginterrupt(signal.SIGCHLD, False)

        def __waitForProcess(process, timeout):
            startTime = time.time()
            endTime = startTime + timeout
            while (time.time() < endTime) and (process.poll() is None):
                # time.sleep() is interrupted by signals,
                # so the loop will continue when child process' state is changed
                remainingTimeout = endTime - time.time()
                if remainingTimeout > 0:
                    time.sleep(remainingTimeout)
    else:
    # dirty hack for BSD-like systems (e.g. MacOS): instead of interruptible time.sleep we use
    # "spin-lock" due to fact that on MacOS enabling time.sleep interrupts by SIGCHLD signal
    # breaks scons - it says "system call interrupted" and stops
        def __waitForProcess(process, timeout):
            startTime = time.time()
            endTime = startTime + timeout
            while (time.time() < endTime) and (process.poll() is None):
                time.sleep(0.1)

    if sys.platform == 'cygwin':
        _PS_CALL_CMD = ['ps', '-e']
    else:
        _PS_CALL_CMD = ['ps', '-A', '-o', 'pid,ppid']

    def _listAllProcesses():
        out = _callWithCheck('Cannot get the list of running processes: ps rc = {0}, '
                             'output = {1}', _PS_CALL_CMD)
        lines = out.splitlines()
        if not re.match(r'\s*PID\s+PPID', lines[0]):
            raise UserError('Bad ps output header: {0}'.format(lines[0]))
        for line in lines[1:]:
            try:
                yield [int(x) for x in re.findall(r'(\d+)', line)[:2]]
            except ValueError:
                raise UserError('Bad line in ps output: {0}'.format(line.strip()))
        
    ACTION_SIGNALS = {ProcessAction.SUSPEND: [signal.SIGSTOP],
                      ProcessAction.TERMINATE: [signal.SIGTERM, signal.SIGKILL],
                      ProcessAction.RESUME: [signal.SIGCONT]}
    def _performAction(pid, action):
        for sigNumber in ACTION_SIGNALS[action]:
            try:
                os.kill(pid, sigNumber)
            except OSError, e:
                if e.errno != errno.ESRCH:
                    raise UserError('Cannot {2} PID {0}: {1}'.format(pid, e, action))
            except BaseException, e:
                raise UserError('Cannot {2} PID {0}: {1}'.format(pid, e, action))

else:
    raise ImportError('Unsupported OS: %s' % os.name)

def _getRunningProcesses():
    ''' returns a dict mapping parent pid to a list of children pids '''
    result = collections.defaultdict(list)
    for pid, ppid in _listAllProcesses():
        result[ppid].append(pid)
    return result

def killProcessTree(proc):
    killQueue = collections.deque([proc.pid])
    while killQueue:
        target = killQueue.popleft()
        # first STOP the target so it won't spawn new children
        _performAction(target, ProcessAction.SUSPEND)
        # now get its children, add them to the end of kill queue and kill the target
        try:
            try:
                killQueue.extend(_getRunningProcesses()[target])
            finally:
                _performAction(target, ProcessAction.TERMINATE)
        finally:
            _performAction(target, ProcessAction.RESUME)

def waitForProcess(process, timeout=None):
    if timeout is None:
        try:
            process.wait()
        except OSError, e:
            if e.errno != errno.ECHILD:
                raise
    else:
        __waitForProcess(process, timeout)