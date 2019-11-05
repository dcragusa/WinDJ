import os
import sys
from cx_Freeze import setup, Executable

PYTHON_INSTALL_DIR = os.path.dirname(os.path.dirname(os.__file__))
os.environ['TCL_LIBRARY'] = os.path.join(PYTHON_INSTALL_DIR, 'tcl', 'tcl8.6')
os.environ['TK_LIBRARY'] = os.path.join(PYTHON_INSTALL_DIR, 'tcl', 'tk8.6')

build_exe_options = {
    'build_exe': 'setup_dj',
    'packages': [
        'os', 'queue', 'threading', 'pyWinhook', 'tkinter', 'multiprocessing', 'configparser', 'helper'
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
    name='dj',
    version='1',
    description='dj',
    options={'build_exe': build_exe_options},
    executables=[Executable('dj.py', base=base)]
)
