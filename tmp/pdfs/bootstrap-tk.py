from pathlib import Path
import ctypes
import os
import runpy
import sys

runtime = (Path(sys.executable).parent.parent / "tk-runtime").resolve()
dlls = os.add_dll_directory(str(runtime / "DLLs"))
sys.path[:0] = [str(runtime / "Lib"), str(runtime / "DLLs")]
os.environ["TCL_LIBRARY"] = (runtime / "tcl/tcl8.6").as_posix()
os.environ["TK_LIBRARY"] = (runtime / "tcl/tk8.6").as_posix()
# Embedded Python tidak menyiapkan lokasi executable untuk Tcl.
tcl = ctypes.WinDLL(str(runtime / "DLLs/tcl86t.dll"))
tcl.Tcl_FindExecutable.argtypes = [ctypes.c_char_p]
tcl.Tcl_FindExecutable(str(Path(sys.executable).resolve()).encode())
import tkinter
tcl.Tcl_CreateInterp.restype = ctypes.c_void_p
tcl.Tcl_Eval.argtypes = [ctypes.c_void_p, ctypes.c_char_p]
tcl.Tcl_DeleteInterp.argtypes = [ctypes.c_void_p]
awal = tcl.Tcl_CreateInterp()
tcl.Tcl_Eval(awal, b"pwd; encoding system; file exists C:/Windows")
tcl.Tcl_DeleteInterp(awal)
sys.path.insert(0, str(Path(__file__).parent / "bab12-code"))
sys.path.insert(0, str(Path(__file__).parent / "bab13-code"))
tujuan = sys.argv[1]
sys.argv = [tujuan] + sys.argv[2:]
runpy.run_path(tujuan, run_name="__main__")
