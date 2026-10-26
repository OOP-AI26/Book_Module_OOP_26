from datetime import date

from perpustakaan import Anggota, BukuCetak, Peminjaman
from perpustakaan.kesalahan import DataTidakValidError, PeminjamanSelesaiError


buku = BukuCetak("B001", "Dasar OOP")
buku.judul = "OOP dengan Python"
print(buku)
try:
    buku.judul = "   "
except DataTidakValidError as exc:
    print("Ditolak:", exc)
print("Judul tetap:", buku.judul)
try:
    buku.kode = "B999"
except AttributeError:
    print("Kode hanya dapat dibaca.")

ani = Anggota("M001", "Ani")
pinjam = Peminjaman("P001", ani, buku, date(2026, 10, 27))
print("Aktif:", pinjam.aktif)
pinjam.kembalikan(date(2026, 11, 2))
print("Aktif setelah kembali:", pinjam.aktif)
try:
    pinjam.kembalikan(date(2026, 11, 3))
except PeminjamanSelesaiError as exc:
    print("Ditolak:", exc)
