"""Tests for the optional compiler-launcher variables CC_LAUNCHER / CXX_LAUNCHER.

A toolchain or site can set these to a launcher such as ccache or sccache; they
are prefixed to the *compiler* invocation across all three build surfaces:

  * native SCons compiles  -> $CC_LAUNCHER/$CXX_LAUNCHER lead the C*COM strings
    (tools/cc.py, tools/c++.py);
  * CMake  -> routed via -DCMAKE_<LANG>_COMPILER_LAUNCHER (pieces/cmake.py), so
    CMAKE_<LANG>_COMPILER stays a clean path and the compiler probe is unaffected;
  * AutoMake -> folded into CC=/CXX= passed to configure (pieces/automake.py),
    since autotools has no launcher concept.

Both default to empty, so they add nothing to any command line unless set.
These tests pin the defaults and the native C*COM wiring. The CMake and
AutoMake paths are covered by the compiler_launcher gold tests, which build
through a logging launcher.
"""
import os

import pytest

import parts.settings as parts_settings


PARTS_TOOLS = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..', '..', 'src', 'parts', 'tools')
)


@pytest.fixture
def env():
    # toolchain=[] -> compiler-less base env, then apply the generic cc/c++ tools
    # from the working tree so we exercise their generate() defaults (where the
    # launcher vars and C*COM strings are set), not a platform compiler override.
    env = parts_settings.DefaultSettings().Environment(toolchain=[])
    env.Tool('cc', toolpath=[PARTS_TOOLS])
    env.Tool('c++', toolpath=[PARTS_TOOLS])
    return env


class TestDefaults:
    def test_launchers_default_empty(self, env):
        assert env['CC_LAUNCHER'] == ''
        assert env['CXX_LAUNCHER'] == ''

    @pytest.mark.parametrize('com,prefix', [
        ('CCCOM', '$CC_LAUNCHER ${TEMPFILE("$CC '),
        ('SHCCCOM', '$CC_LAUNCHER ${TEMPFILE("$SHCC '),
        ('CXXCOM', '$CXX_LAUNCHER ${TEMPFILE("$CXX '),
        ('SHCXXCOM', '$CXX_LAUNCHER ${TEMPFILE("$SHCXX '),
    ])
    def test_launcher_leads_compiler_outside_tempfile(self, env, com, prefix):
        # the launcher goes in front of TEMPFILE, not inside it: a response file
        # keeps only the first word of the command on the command line, so a
        # launcher inside it would run with just @file and no compiler
        assert env[com].startswith(prefix)


class TestNativeApplied:
    def test_empty_cc_launcher_is_noop(self, env):
        # empty launcher -> the compile command is just the bare compiler
        assert env.subst('$CC_LAUNCHER $CC').split() == env.subst('$CC').split()
        assert env.subst('$CXX_LAUNCHER $CXX').split() == env.subst('$CXX').split()

    def test_set_cc_launcher_prefixes_compiler(self, env):
        env['CC_LAUNCHER'] = 'ccache'
        tokens = env.subst('$CC_LAUNCHER $CC').split()
        assert tokens[0] == 'ccache'
        assert tokens[1:] == env.subst('$CC').split()

    def test_set_cxx_launcher_prefixes_compiler(self, env):
        env['CXX_LAUNCHER'] = 'sccache'
        tokens = env.subst('$CXX_LAUNCHER $CXX').split()
        assert tokens[0] == 'sccache'
        assert tokens[1:] == env.subst('$CXX').split()

    def test_shared_variants_honor_launcher(self, env):
        env['CC_LAUNCHER'] = 'ccache'
        env['CXX_LAUNCHER'] = 'ccache'
        assert env.subst('$CC_LAUNCHER $SHCC').split()[0] == 'ccache'
        assert env.subst('$CXX_LAUNCHER $SHCXX').split()[0] == 'ccache'
