import subprocess,sys

if sys.platform == 'win32':
    sys.exit(subprocess.call("launch_tests.bat"))
else:
    sys.exit(subprocess.call("./launch_tests.sh"))