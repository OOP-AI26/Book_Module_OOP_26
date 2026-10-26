import ctypes as c
from pathlib import Path
import os
import sys

p = (Path(sys.executable).parent.parent / "tk-runtime").resolve()
os.environ["TCL_LIBRARY"] = (p / "tcl/tcl8.6").as_posix()
os.environ["TK_LIBRARY"] = (p / "tcl/tk8.6").as_posix()
sys.path[:0] = [str(p / "Lib"), str(p / "DLLs")]
dll = os.add_dll_directory(str(p / "DLLs"))
import tkinter
t = c.WinDLL(str(p / "DLLs/tcl86t.dll"))
t.Tcl_FindExecutable.argtypes = [c.c_char_p]
t.Tcl_FindExecutable(str(Path(sys.executable).resolve()).encode())
t.Tcl_CreateInterp.restype = c.c_void_p
t.Tcl_Eval.argtypes = [c.c_void_p, c.c_char_p]
t.Tcl_GetStringResult.argtypes = [c.c_void_p]
t.Tcl_GetStringResult.restype = c.c_char_p
t.Tcl_DeleteInterp.argtypes = [c.c_void_p]
t.Tcl_Init.argtypes = [c.c_void_p]
i = t.Tcl_CreateInterp()
for script in ["file exists C:/Windows", "pwd", "encoding system", "info loaded",
               f"file exists {{{(p/'tcl/tcl8.6/init.tcl').as_posix()}}}",
               "file exists {C:/Users/ABDULL~1/AppData/Local/Temp/oop-book-reference-tools/tk-runtime/tcl/tcl8.6/init.tcl}",
               "info patchlevel", f"source {{{(p/'tcl/tcl8.6/init.tcl').as_posix()}}}"]:
    rc = t.Tcl_Eval(i, script.encode())
    print(rc, t.Tcl_GetStringResult(i).decode(errors="replace"))
print("INIT", t.Tcl_Init(i), t.Tcl_GetStringResult(i).decode(errors="replace"))
t.Tcl_DeleteInterp(i)
r = tkinter.Tk()
r.withdraw()
print("TK OK")
r.destroy()
