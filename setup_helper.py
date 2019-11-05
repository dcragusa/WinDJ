import os
import sys
from cx_Freeze import setup, Executable

PYTHON_INSTALL_DIR = os.path.dirname(os.path.dirname(os.__file__))
os.environ['TCL_LIBRARY'] = os.path.join(PYTHON_INSTALL_DIR, 'tcl', 'tcl8.6')
os.environ['TK_LIBRARY'] = os.path.join(PYTHON_INSTALL_DIR, 'tcl', 'tk8.6')

build_exe_options = {
    'build_exe': 'setup_helper',
    'packages': [
        'os', 'sys', 'queue', 'threading', 'pyWinhook', 'tkinter', 'multiprocessing'
    ],
    'include_files': [
        'favicon.ico',
        os.path.join(PYTHON_INSTALL_DIR, 'DLLs', 'tcl86t.dll'),
        os.path.join(PYTHON_INSTALL_DIR, 'DLLs', 'tk86t.dll')
    ],
}

base = None
if sys.platform == 'win32':
    base = 'Win32GUI'

setup(
    name='helper',
    version='1',
    description='helper',
    options={'build_exe': build_exe_options},
    executables=[Executable('helper.py', base=base)]
)
