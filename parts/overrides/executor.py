from SCons.Executor import TSList

def def_TSList___iter__(klass):
    def __iter__(self):
        return self.func().__iter__()
    klass.__iter__ = __iter__

def_TSList___iter__(TSList)

from SCons.Util import UniqueList
from collections import UserList
def def_UniqueList___iter__(klass):
    def __iter__(self):
        self._UniqueList__make_unique()
        return UserList.__iter__(self)
    klass.__iter__ = __iter__
def_UniqueList___iter__(UniqueList)

# vim: set et ts=4 sw=4 ai ft=python :

