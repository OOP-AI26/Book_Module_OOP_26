from datetime import date
from pathlib import Path

from perpustakaan import (
    Anggota, BukuCetak, EBook, Perpustakaan,
    PenyimpananJSON, PerpustakaanError,
)


def main():
    path = Path(__file__).resolve().parent / "data" / "perpustakaan.json"
    perpus = Perpustakaan(PenyimpananJSON(path))
    try:
        perpus.muat()
    except PerpustakaanError as exc:
        print("Data tidak dimuat:", exc)
        return 1  # tidak melanjutkan dengan data kosong lalu menimpa file

    while True:
        print("\n1 Buku | 2 Tambah buku | 3 Tambah anggota")
        print("4 Pinjam | 5 Kembali | 6 Riwayat | 0 Simpan dan keluar")
        try:
            pilihan = input("Pilihan: ").strip()
            if pilihan == "1":
                for buku in perpus.daftar_buku():
                    status = "tersedia" if perpus.tersedia(buku.kode) else "dipinjam"
                    print(buku, "-", status)
            elif pilihan == "2":
                kode = input("Kode buku: ")
                judul = input("Judul: ")
                jenis = input("Jenis (cetak/ebook): ").strip().lower()
                kelas = {"cetak": BukuCetak, "ebook": EBook}.get(jenis)
                if kelas is None:
                    raise ValueError("Jenis harus cetak atau ebook.")
                perpus.tambah_buku(kelas(kode, judul))
                print("Buku terdaftar.")
            elif pilihan == "3":
                identitas = input("ID anggota: ")
                nama = input("Nama: ")
                perpus.tambah_anggota(Anggota(identitas, nama))
                print("Anggota terdaftar.")
            elif pilihan == "4":
                anggota = input("ID anggota: ")
                buku = input("Kode buku: ")
                tanggal = date.fromisoformat(input("Tanggal YYYY-MM-DD: ").strip())
                pinjam = perpus.pinjamkan(anggota, buku, tanggal)
                print("Berhasil:", pinjam.id_pinjam,
                      "jatuh tempo", pinjam.tanggal_jatuh_tempo)
            elif pilihan == "5":
                identitas = input("ID peminjaman: ")
                tanggal = date.fromisoformat(input("Tanggal YYYY-MM-DD: ").strip())
                perpus.kembalikan(identitas, tanggal)
                print("Pengembalian tercatat.")
            elif pilihan == "6":
                for p in perpus.daftar_peminjaman():
                    status = "aktif" if p.aktif else "selesai"
                    print(p.id_pinjam, p.anggota.nama, p.buku.kode, status)
            elif pilihan == "0":
                perpus.simpan()
                print("Data tersimpan.")
                return 0
            else:
                print("Pilihan tidak dikenal.")
        except (PerpustakaanError, ValueError) as exc:
            print("Ditolak:", exc)
        except (EOFError, KeyboardInterrupt):
            print("\nInput dihentikan; perubahan sesi ini belum disimpan.")
            return 1


if __name__ == "__main__":
    raise SystemExit(main())
