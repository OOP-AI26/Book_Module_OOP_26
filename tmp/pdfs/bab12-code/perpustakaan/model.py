from abc import ABC, abstractmethod
from datetime import date, datetime, timedelta

from .kesalahan import DataTidakValidError, PeminjamanSelesaiError


def teks_wajib(nilai, label):
    if not isinstance(nilai, str) or not nilai.strip():
        raise DataTidakValidError(f"{label} harus berupa teks yang terisi.")
    return nilai.strip()


def tanggal_valid(nilai):
    if not isinstance(nilai, date) or isinstance(nilai, datetime):
        raise DataTidakValidError("Tanggal harus berupa object date.")
    return nilai


class Buku(ABC):
    JENIS = ""

    def __init__(self, kode, judul):
        self._kode = teks_wajib(kode, "Kode buku")
        self.judul = judul

    @property
    def kode(self):
        return self._kode

    @property
    def judul(self):
        return self._judul

    @judul.setter
    def judul(self, nilai):
        self._judul = teks_wajib(nilai, "Judul buku")

    @abstractmethod
    def lama_pinjam(self):
        """Mengembalikan lama pinjam dalam hari."""

    def ke_data(self):
        return {"kode": self.kode, "judul": self.judul, "jenis": self.JENIS}

    def __str__(self):
        return f"[{self.kode}] {self.judul}"


class BukuCetak(Buku):
    JENIS = "cetak"

    def lama_pinjam(self):
        return 14


class EBook(Buku):
    JENIS = "ebook"

    def lama_pinjam(self):
        return 7


class Anggota:
    def __init__(self, id_anggota, nama):
        self._id_anggota = teks_wajib(id_anggota, "ID anggota")
        self.nama = nama

    @property
    def id_anggota(self):
        return self._id_anggota

    @property
    def nama(self):
        return self._nama

    @nama.setter
    def nama(self, nilai):
        self._nama = teks_wajib(nilai, "Nama anggota")

    def info(self):
        return f"{self.id_anggota} - {self.nama}"

    def ke_data(self):
        return {"id_anggota": self.id_anggota, "nama": self.nama}


class Peminjaman:
    def __init__(self, id_pinjam, anggota, buku, tanggal, jatuh_tempo=None):
        if not isinstance(anggota, Anggota) or not isinstance(buku, Buku):
            raise DataTidakValidError("Peminjaman memerlukan anggota dan buku.")
        self._id_pinjam = teks_wajib(id_pinjam, "ID peminjaman")
        self._anggota = anggota
        self._buku = buku
        self._tanggal_pinjam = tanggal_valid(tanggal)
        if jatuh_tempo is None:
            try:
                jatuh_tempo = tanggal + timedelta(days=buku.lama_pinjam())
            except OverflowError as exc:
                raise DataTidakValidError("Tanggal di luar jangkauan.") from exc
        self._tanggal_jatuh_tempo = tanggal_valid(jatuh_tempo)
        if jatuh_tempo < tanggal:
            raise DataTidakValidError("Jatuh tempo mendahului tanggal pinjam.")
        self._tanggal_kembali = None

    @property
    def id_pinjam(self):
        return self._id_pinjam

    @property
    def anggota(self):
        return self._anggota

    @property
    def buku(self):
        return self._buku

    @property
    def tanggal_pinjam(self):
        return self._tanggal_pinjam

    @property
    def tanggal_jatuh_tempo(self):
        return self._tanggal_jatuh_tempo

    @property
    def tanggal_kembali(self):
        return self._tanggal_kembali

    @property
    def aktif(self):
        return self.tanggal_kembali is None

    def kembalikan(self, tanggal):
        if not self.aktif:
            raise PeminjamanSelesaiError("Peminjaman sudah selesai.")
        tanggal = tanggal_valid(tanggal)
        if tanggal < self.tanggal_pinjam:
            raise DataTidakValidError("Pengembalian mendahului tanggal pinjam.")
        self._tanggal_kembali = tanggal

    def ke_data(self):
        kembali = self.tanggal_kembali
        return {
            "id_pinjam": self.id_pinjam,
            "id_anggota": self.anggota.id_anggota,
            "kode_buku": self.buku.kode,
            "tanggal_pinjam": self.tanggal_pinjam.isoformat(),
            "tanggal_jatuh_tempo": self.tanggal_jatuh_tempo.isoformat(),
            "tanggal_kembali": kembali.isoformat() if kembali else None,
        }
