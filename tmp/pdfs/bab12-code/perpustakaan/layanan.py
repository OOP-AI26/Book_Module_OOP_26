from datetime import date

from .kesalahan import (
    PerpustakaanError, DataTidakValidError, DataTidakDitemukanError,
    BukuSedangDipinjamError, DataRusakError,
)
from .model import Anggota, Buku, BukuCetak, EBook, Peminjaman, teks_wajib
from .penyimpanan import Penyimpanan


class Perpustakaan:
    def __init__(self, penyimpanan: Penyimpanan):
        self._penyimpanan = penyimpanan
        self._buku = {}
        self._anggota = {}
        self._peminjaman = {}
        self._nomor_pinjam_berikutnya = 1

    def tambah_buku(self, buku):
        if not isinstance(buku, Buku):
            raise DataTidakValidError("Data harus berupa object Buku.")
        if buku.kode in self._buku:
            raise DataTidakValidError("Kode buku sudah terdaftar.")
        self._buku[buku.kode] = buku

    def tambah_anggota(self, anggota):
        if not isinstance(anggota, Anggota):
            raise DataTidakValidError("Data harus berupa object Anggota.")
        if anggota.id_anggota in self._anggota:
            raise DataTidakValidError("ID anggota sudah terdaftar.")
        self._anggota[anggota.id_anggota] = anggota

    def _cari(self, koleksi, identitas, label):
        identitas = teks_wajib(identitas, label)
        if identitas not in koleksi:
            raise DataTidakDitemukanError(f"{label} tidak ditemukan.")
        return koleksi[identitas]

    def tersedia(self, kode_buku):
        buku = self._cari(self._buku, kode_buku, "Buku")
        return not any(
            p.aktif and p.buku.kode == buku.kode
            for p in self._peminjaman.values()
        )

    def pinjamkan(self, id_anggota, kode_buku, tanggal):
        anggota = self._cari(self._anggota, id_anggota, "Anggota")
        buku = self._cari(self._buku, kode_buku, "Buku")
        if not self.tersedia(buku.kode):
            raise BukuSedangDipinjamError("Buku masih dipinjam.")
        identitas = f"P{self._nomor_pinjam_berikutnya:03d}"
        pinjam = Peminjaman(identitas, anggota, buku, tanggal)
        self._peminjaman[identitas] = pinjam
        self._nomor_pinjam_berikutnya += 1
        return pinjam

    def kembalikan(self, id_pinjam, tanggal):
        pinjam = self._cari(self._peminjaman, id_pinjam, "Peminjaman")
        pinjam.kembalikan(tanggal)

    def daftar_buku(self):
        return list(self._buku.values())

    def daftar_anggota(self):
        return list(self._anggota.values())

    def daftar_peminjaman(self, aktif_saja=False):
        return [p for p in self._peminjaman.values()
                if not aktif_saja or p.aktif]

    def simpan(self):
        data = {
            "versi": 1,
            "nomor_pinjam_berikutnya": self._nomor_pinjam_berikutnya,
            "buku": [b.ke_data() for b in self._buku.values()],
            "anggota": [a.ke_data() for a in self._anggota.values()],
            "peminjaman": [p.ke_data() for p in self._peminjaman.values()],
        }
        self._penyimpanan.simpan(data)

    def muat(self):
        try:
            data = self._penyimpanan.muat()
        except FileNotFoundError:
            return  # pertama kali dipakai: belum ada data di disk

        # Susun keadaan sementara; keadaan lama tetap utuh jika data salah.
        try:
            wajib = {"versi", "nomor_pinjam_berikutnya", "buku",
                     "anggota", "peminjaman"}
            if not isinstance(data, dict) or set(data) != wajib:
                raise DataTidakValidError("Field data tidak lengkap.")
            if type(data["versi"]) is not int or data["versi"] != 1:
                raise DataTidakValidError("Versi data tidak didukung.")
            for nama in ("buku", "anggota", "peminjaman"):
                if not isinstance(data[nama], list):
                    raise DataTidakValidError("Koleksi harus berupa list.")
            baru = Perpustakaan(self._penyimpanan)
            jenis_buku = {"cetak": BukuCetak, "ebook": EBook}
            for d in data["buku"]:
                kelas = jenis_buku[d["jenis"]]
                baru.tambah_buku(kelas(d["kode"], d["judul"]))
            for d in data["anggota"]:
                baru.tambah_anggota(Anggota(d["id_anggota"], d["nama"]))
            nomor_terbesar = 0
            for d in data["peminjaman"]:
                p = Peminjaman(
                    d["id_pinjam"], baru._anggota[d["id_anggota"]],
                    baru._buku[d["kode_buku"]],
                    date.fromisoformat(d["tanggal_pinjam"]),
                    date.fromisoformat(d["tanggal_jatuh_tempo"]),
                )
                if d["tanggal_kembali"] is not None:
                    p.kembalikan(date.fromisoformat(d["tanggal_kembali"]))
                identitas = p.id_pinjam
                if (not identitas.startswith("P")
                        or not identitas[1:].isdigit()
                        or identitas in baru._peminjaman):
                    raise DataTidakValidError("ID peminjaman tidak sah.")
                if p.aktif and not baru.tersedia(p.buku.kode):
                    raise DataTidakValidError("Buku dipinjam dua kali.")
                baru._peminjaman[identitas] = p
                nomor_terbesar = max(nomor_terbesar, int(identitas[1:]))
            nomor = data["nomor_pinjam_berikutnya"]
            if type(nomor) is not int or nomor <= nomor_terbesar:
                raise DataTidakValidError("Penomoran peminjaman tidak sah.")
            baru._nomor_pinjam_berikutnya = nomor
        except (KeyError, TypeError, ValueError, PerpustakaanError) as exc:
            raise DataRusakError("Struktur data perpustakaan tidak sah.") from exc

        self._buku = baru._buku
        self._anggota = baru._anggota
        self._peminjaman = baru._peminjaman
        self._nomor_pinjam_berikutnya = baru._nomor_pinjam_berikutnya
