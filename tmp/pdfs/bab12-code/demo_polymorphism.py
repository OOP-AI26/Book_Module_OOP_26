from datetime import date

from perpustakaan import Anggota, BukuCetak, EBook, Peminjaman


ani = Anggota("M001", "Ani")
koleksi = [BukuCetak("B001", "Dasar OOP"), EBook("E001", "Dasar Python")]
for nomor, buku in enumerate(koleksi, start=1):
    pinjam = Peminjaman(f"P{nomor:03d}", ani, buku, date(2026, 10, 27))
    print(buku.kode, buku.lama_pinjam(), "hari, jatuh tempo",
          pinjam.tanggal_jatuh_tempo)
