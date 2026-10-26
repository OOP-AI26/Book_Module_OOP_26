class PerpustakaanError(Exception):
    """Induk kesalahan yang dapat ditampilkan oleh antarmuka."""


class DataTidakValidError(PerpustakaanError):
    pass


class DataTidakDitemukanError(PerpustakaanError):
    pass


class BukuSedangDipinjamError(PerpustakaanError):
    pass


class PeminjamanSelesaiError(PerpustakaanError):
    pass


class DataRusakError(PerpustakaanError):
    pass


class PenyimpananError(PerpustakaanError):
    pass
