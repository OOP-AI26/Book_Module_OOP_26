from datetime import date
from pathlib import Path
import tkinter as tk
from tkinter import messagebox, ttk

from perpustakaan import (
    Anggota, BukuCetak, EBook, Perpustakaan,
    PerpustakaanError, PenyimpananJSON,
)


def baca_tanggal(teks):
    teks = teks.strip()
    try:
        tanggal = date.fromisoformat(teks)
        if tanggal.isoformat() != teks:
            raise ValueError
    except ValueError as exc:
        raise ValueError("Gunakan tanggal sah berformat YYYY-MM-DD.") from exc
    return tanggal


class AplikasiPerpustakaan:
    def __init__(self, root, perpus):
        self.root = root
        self.perpus = perpus
        self.berubah = False
        root.title("Sistem Peminjaman Perpustakaan")
        root.geometry("1100x760")
        root.minsize(950, 650)

        self.kode = tk.StringVar(root)
        self.judul = tk.StringVar(root)
        self.jenis = tk.StringVar(root, value="cetak")
        self.id_anggota = tk.StringVar(root)
        self.nama = tk.StringVar(root)
        self.anggota_dipilih = tk.StringVar(root)
        self.buku_dipilih = tk.StringVar(root)
        self.tanggal = tk.StringVar(root, value=date.today().isoformat())
        self.status = tk.StringVar(root, value="Siap. Belum ada perubahan.")

        ttk.Label(root, text="Sistem Peminjaman Perpustakaan",
                  font=("TkDefaultFont", 16, "bold")).pack(pady=(12, 4))
        self.tab = ttk.Notebook(root)
        self.tab.pack(fill="both", expand=True, padx=12, pady=8)
        self._buat_tab_buku()
        self._buat_tab_anggota()
        self._buat_tab_pinjam()

        bawah = ttk.Frame(root, padding=(12, 0, 12, 12))
        bawah.pack(fill="x")
        ttk.Label(bawah, textvariable=self.status).pack(side="left")
        ttk.Button(bawah, text="Tutup", command=self.tutup).pack(side="right")
        ttk.Button(bawah, text="Simpan", command=self.simpan).pack(
            side="right", padx=8)
        root.bind("<Control-s>", self.simpan)
        root.protocol("WM_DELETE_WINDOW", self.tutup)
        self.segarkan()

    def _halaman(self, judul):
        halaman = ttk.Frame(self.tab, padding=12)
        self.tab.add(halaman, text=judul)
        return halaman

    def _isian(self, parent, label, variabel, kolom, lebar=18):
        ttk.Label(parent, text=label).grid(
            row=0, column=kolom, sticky="w", pady=(0, 4))
        isian = ttk.Entry(parent, textvariable=variabel, width=lebar)
        isian.grid(row=1, column=kolom, sticky="ew", padx=(0, 8))
        parent.columnconfigure(kolom, weight=1)
        return isian

    def _tabel(self, parent, kolom):
        wadah = ttk.Frame(parent)
        wadah.pack(fill="both", expand=True, pady=(12, 0))
        wadah.rowconfigure(0, weight=1)
        wadah.columnconfigure(0, weight=1)
        nama = [k[0] for k in kolom]
        tabel = ttk.Treeview(wadah, columns=nama, show="headings",
                             selectmode="browse")
        for nama, judul, lebar in kolom:
            tabel.heading(nama, text=judul)
            tabel.column(nama, width=lebar, minwidth=60, anchor="w")
        vertikal = ttk.Scrollbar(wadah, orient="vertical", command=tabel.yview)
        horizontal = ttk.Scrollbar(wadah, orient="horizontal", command=tabel.xview)
        tabel.configure(yscrollcommand=vertikal.set,
                        xscrollcommand=horizontal.set)
        tabel.grid(row=0, column=0, sticky="nsew")
        vertikal.grid(row=0, column=1, sticky="ns")
        horizontal.grid(row=1, column=0, sticky="ew")
        return tabel

    def _buat_tab_buku(self):
        halaman = self._halaman("Buku")
        form = ttk.Frame(halaman)
        form.pack(fill="x")
        self._isian(form, "Kode buku", self.kode, 0, 12)
        self._isian(form, "Judul", self.judul, 1, 36)
        ttk.Label(form, text="Jenis").grid(row=0, column=2, sticky="w")
        ttk.Combobox(form, textvariable=self.jenis, values=("cetak", "ebook"),
                     state="readonly", width=12).grid(row=1, column=2, padx=8)
        ttk.Button(form, text="Daftarkan buku", command=self.tambah_buku).grid(
            row=1, column=3)
        self.tabel_buku = self._tabel(halaman, [
            ("kode", "Kode", 100), ("judul", "Judul", 380),
            ("jenis", "Jenis", 100), ("status", "Status", 110),
        ])
        self.tabel_buku.bind("<<TreeviewSelect>>", self.pilih_buku)

    def _buat_tab_anggota(self):
        halaman = self._halaman("Anggota")
        form = ttk.Frame(halaman)
        form.pack(fill="x")
        self._isian(form, "ID anggota", self.id_anggota, 0, 14)
        self._isian(form, "Nama", self.nama, 1, 40)
        ttk.Button(form, text="Daftarkan anggota", command=self.tambah_anggota).grid(
            row=1, column=2)
        self.tabel_anggota = self._tabel(halaman, [
            ("id", "ID anggota", 130), ("nama", "Nama", 500),
        ])

    def _buat_tab_pinjam(self):
        halaman = self._halaman("Peminjaman")
        form = ttk.Frame(halaman)
        form.pack(fill="x")
        for kolom, label in enumerate(("ID anggota", "Kode buku tersedia")):
            ttk.Label(form, text=label).grid(row=0, column=kolom, sticky="w")
        self.pilihan_anggota = ttk.Combobox(
            form, textvariable=self.anggota_dipilih, state="readonly", width=16)
        self.pilihan_anggota.grid(row=1, column=0, padx=(0, 8))
        self.pilihan_buku = ttk.Combobox(
            form, textvariable=self.buku_dipilih, state="readonly", width=16)
        self.pilihan_buku.grid(row=1, column=1, padx=(0, 8))
        self._isian(form, "Tanggal transaksi (YYYY-MM-DD)", self.tanggal, 2, 20)
        ttk.Button(form, text="Pinjam", command=self.pinjam).grid(
            row=1, column=3, padx=4)
        ttk.Button(form, text="Kembalikan pilihan", command=self.kembalikan).grid(
            row=1, column=4)
        ttk.Label(halaman, text="Untuk pengembalian, pilih satu baris riwayat "
                  "dan isi tanggal transaksi.").pack(anchor="w", pady=(12, 0))
        self.tabel_pinjam = self._tabel(halaman, [
            ("id", "ID pinjam", 80), ("anggota", "Anggota", 90),
            ("buku", "Buku", 80), ("pinjam", "Tanggal pinjam", 115),
            ("jatuh", "Jatuh tempo", 115), ("kembali", "Tanggal kembali", 120),
            ("status", "Status", 85),
        ])

    def _isi_tabel(self, tabel, baris):
        dipilih = tabel.selection()
        tabel.delete(*tabel.get_children())
        for identitas, nilai in baris:
            tabel.insert("", "end", iid=identitas, values=nilai)
        if dipilih and tabel.exists(dipilih[0]):
            tabel.selection_set(dipilih[0])

    def segarkan(self):
        buku = self.perpus.daftar_buku()
        anggota = self.perpus.daftar_anggota()
        self._isi_tabel(self.tabel_buku, [
            (b.kode, (b.kode, b.judul, b.JENIS,
                      "tersedia" if self.perpus.tersedia(b.kode) else "dipinjam"))
            for b in buku
        ])
        self._isi_tabel(self.tabel_anggota, [
            (a.id_anggota, (a.id_anggota, a.nama)) for a in anggota
        ])
        self._isi_tabel(self.tabel_pinjam, [
            (p.id_pinjam, (p.id_pinjam, p.anggota.id_anggota, p.buku.kode,
                          p.tanggal_pinjam.isoformat(),
                          p.tanggal_jatuh_tempo.isoformat(),
                          p.tanggal_kembali.isoformat() if p.tanggal_kembali else "-",
                          "aktif" if p.aktif else "selesai"))
            for p in self.perpus.daftar_peminjaman()
        ])
        id_anggota = [a.id_anggota for a in anggota]
        tersedia = [b.kode for b in buku if self.perpus.tersedia(b.kode)]
        self.pilihan_anggota["values"] = id_anggota
        self.pilihan_buku["values"] = tersedia
        if self.anggota_dipilih.get() not in id_anggota:
            self.anggota_dipilih.set("")
        if self.buku_dipilih.get() not in tersedia:
            self.buku_dipilih.set("")

    def _jalankan(self, aksi, pesan):
        try:
            aksi()
        except (PerpustakaanError, ValueError) as exc:
            messagebox.showerror("Operasi ditolak", str(exc), parent=self.root)
            return False
        self.berubah = True
        self.segarkan()
        self.status.set(f"{pesan} Perubahan belum disimpan.")
        return True

    def tambah_buku(self):
        def aksi():
            kelas = {"cetak": BukuCetak, "ebook": EBook}.get(self.jenis.get())
            if kelas is None:
                raise ValueError("Pilih jenis cetak atau ebook.")
            self.perpus.tambah_buku(kelas(self.kode.get(), self.judul.get()))
        if self._jalankan(aksi, "Buku terdaftar."):
            self.kode.set("")
            self.judul.set("")

    def tambah_anggota(self):
        aksi = lambda: self.perpus.tambah_anggota(
            Anggota(self.id_anggota.get(), self.nama.get()))
        if self._jalankan(aksi, "Anggota terdaftar."):
            self.id_anggota.set("")
            self.nama.set("")

    def pinjam(self):
        def aksi():
            if not self.anggota_dipilih.get() or not self.buku_dipilih.get():
                raise ValueError("Pilih anggota dan buku yang tersedia.")
            self.perpus.pinjamkan(self.anggota_dipilih.get(),
                                  self.buku_dipilih.get(),
                                  baca_tanggal(self.tanggal.get()))
        self._jalankan(aksi, "Peminjaman tercatat.")

    def kembalikan(self):
        def aksi():
            pilihan = self.tabel_pinjam.selection()
            if not pilihan:
                raise ValueError("Pilih satu baris peminjaman.")
            self.perpus.kembalikan(pilihan[0], baca_tanggal(self.tanggal.get()))
        self._jalankan(aksi, "Pengembalian tercatat.")

    def pilih_buku(self, event=None):
        pilihan = self.tabel_buku.selection()
        if pilihan:
            kode = pilihan[0]
            self.buku_dipilih.set(kode if self.perpus.tersedia(kode) else "")

    def simpan(self, event=None):
        try:
            self.perpus.simpan()
        except PerpustakaanError as exc:
            messagebox.showerror("Gagal menyimpan", str(exc), parent=self.root)
            return False
        self.berubah = False
        self.status.set("Data tersimpan.")
        return True

    def tutup(self):
        if self.berubah:
            jawaban = messagebox.askyesnocancel(
                "Simpan perubahan?", "Simpan perubahan sebelum keluar?",
                parent=self.root)
            if jawaban is None:
                return
            if jawaban and not self.simpan():
                return
        self.root.destroy()


def main():
    root = tk.Tk()
    root.withdraw()
    path = Path(__file__).resolve().parent / "data" / "perpustakaan.json"
    perpus = Perpustakaan(PenyimpananJSON(path))
    try:
        perpus.muat()
    except PerpustakaanError as exc:
        messagebox.showerror("Data tidak dimuat", str(exc), parent=root)
        root.destroy()
        return 1
    AplikasiPerpustakaan(root, perpus)
    root.deiconify()
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
