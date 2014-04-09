'''
Helper script that allows working with per-thread Parts logs
'''

import glob
import sys
import datetime

class LogLine(object):
    UNPACK = ['targets', 'sources', 'command']
    __slots__ = ['timestamp', 'event', 'duration'] + UNPACK

    def __init__(self, line, previousLogs=None):
        timestamp, rest = line.split('\t', 1)
        self.timestamp = datetime.datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S.%f')
        if rest.startswith('start'):
            event, targets, sources, command = rest.split('\t')
            self.duration = None
        elif rest.startswith('stop'):
            event = 'stop'
            try:
                previousLogLine = previousLogs[-1]
            except:
                targets, sources, command = None, None, None
            else:
                targets, sources, command = previousLogLine.targets, previousLogLine.sources, \
                                            previousLogLine.command
                previousLogLine.duration = (self.timestamp - previousLogLine.timestamp).\
                                            total_seconds()
        else:
            raise ValueError('unexpected line format: %r' % line)
        self.event = event
        result = {}
        for unpackName in self.UNPACK:
            self.unpack(result, **{unpackName: locals()[unpackName]})
            setattr(self, unpackName, result[unpackName])

    @staticmethod
    def unpack(result, **values):
        newLocals = {'result': result}
        for name, value in values.iteritems():
            try:
                exec 'result["%s"] = %s' % (name, value) in newLocals
            except:
                result[name] = value

    def __str__(self):
        return '%s (%.3f)\t%s\t%s' % (self.timestamp, self.duration, self.event,
                self.command[:40] + ('...' if len(self.command) > 40 else ''))

    def __repr__(self):
        return repr(self.__str__())

def loadLogFile(path):
    temp = []
    with open(path, 'r') as logFile:
        for line in logFile:
            temp.append(LogLine(line.strip(), temp))

    result = []
    for logLine in temp:
        if logLine.event != 'start':
            continue
        if logLine.duration is not None:
            logLine.event = 'done'
        else:
            logLine.duration = float('inf')
        result.append(logLine)
    return result

def main(args):
    if not args:
        print >> sys.stderr, 'Usage: %s logfile-to-load' % sys.argv[0]
        return 1
    result = []
    for arg in args:
        for file in glob.glob(arg):
            result += loadLogFile(file)
    import pdb
    pdb.set_trace()

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
