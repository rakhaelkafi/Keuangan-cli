"""Exception khusus agar error aplikasi mudah dibedakan dari bug."""


class KeuanganError(Exception):
    """Kelas dasar semua error aplikasi ini."""


class DataTidakValidError(KeuanganError):
    """Isi data tidak sesuai aturan (tanggal salah, jumlah bukan angka, dst)."""


class FormatTidakDidukungError(KeuanganError):
    """Ekstensi file selain .csv atau .json."""
