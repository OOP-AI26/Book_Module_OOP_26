from datetime import date

from perpustakaan import Anggota, Buku, BukuCetak, Peminjaman


ani = Anggota("M001", "Ani")
buku = BukuCetak("B001", "Dasar OOP")
pinjam = Peminjaman("P001", ani, buku, date(2026, 10, 27))

print("BukuCetak adalah Buku:", isinstance(buku, Buku))
print("Anggota yang sama:", pinjam.anggota is ani)
print("Buku yang sama:", pinjam.buku is buku)
ani.nama = "Ani Lestari"
print("Peminjam:", pinjam.anggota.nama)
