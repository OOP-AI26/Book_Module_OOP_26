from pathlib import Path
import ctypes as ct
import _msi
import shutil
import subprocess
import tempfile

runtime = Path(tempfile.gettempdir()) / "oop-book-reference-tools"
sumber = runtime / "tcltk.msi"
cab = runtime / "tk-cab1.cab"
mentah = runtime / "tk-cab-files"
tujuan = runtime / "tk-runtime"
mentah.mkdir(exist_ok=True)
tujuan.mkdir(exist_ok=True)

msi = ct.WinDLL("msi")
database, view, record = ct.c_uint(), ct.c_uint(), ct.c_uint()
def periksa(kode):
    if kode:
        raise OSError(kode)
periksa(msi.MsiOpenDatabaseW(str(sumber), None, ct.byref(database)))
periksa(msi.MsiDatabaseOpenViewW(database, "SELECT Data FROM _Streams WHERE Name='cab1.cab'", ct.byref(view)))
periksa(msi.MsiViewExecute(view, 0))
periksa(msi.MsiViewFetch(view, ct.byref(record)))
with cab.open("wb") as file:
    while True:
        buffer = ct.create_string_buffer(65536)
        ukuran = ct.c_uint(len(buffer))
        periksa(msi.MsiRecordReadStream(record, 1, buffer, ct.byref(ukuran)))
        if not ukuran.value:
            break
        file.write(buffer.raw[:ukuran.value])
for handle in (record, view, database):
    msi.MsiCloseHandle(handle)
subprocess.run(["expand.exe", "-F:*", str(cab), str(mentah)], check=True, capture_output=True)

db = _msi.OpenDatabase(str(sumber), _msi.MSIDBOPEN_READONLY)
def baris(sql, lebar):
    v = db.OpenView(sql)
    v.Execute(None)
    r = v.Fetch()
    while r:
        yield tuple(r.GetString(i) for i in range(1, lebar+1))
        r = v.Fetch()

direktori = {id: (induk, nama.split("|")[-1].split(":")[0])
             for id, induk, nama in baris("SELECT Directory, Directory_Parent, DefaultDir FROM Directory", 3)}
komponen = dict(baris("SELECT Component, Directory_ FROM Component", 2))
def path_direktori(id):
    if id == "TARGETDIR":
        return tujuan
    induk, nama = direktori[id]
    path = path_direktori(induk)
    return path if nama == "." else path / nama

jumlah = 0
for id, komponen_id, nama in baris("SELECT File, Component_, FileName FROM File", 3):
    path = path_direktori(komponen[komponen_id]) / nama.split("|")[-1]
    if not path.resolve().is_relative_to(tujuan.resolve()):
        raise ValueError("Tujuan ekstraksi di luar folder runtime.")
    path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(mentah / id, path)
    jumlah += 1
print(f"{jumlah} file Tcl/Tk diekstrak tanpa memasang aplikasi.")
