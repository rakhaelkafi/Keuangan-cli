"""Unit test. Jalankan dari root proyek: python -m unittest discover -s tests -v"""

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from keuangan import analisis, io_utils  # noqa: E402
from keuangan.exceptions import DataTidakValidError, FormatTidakDidukungError  # noqa: E402


def t(tanggal, tipe, kategori, jumlah, desk="x"):
    return io_utils.normalisasi_baris(
        {"tanggal": tanggal, "deskripsi": desk, "kategori": kategori,
         "jumlah": jumlah, "tipe": tipe}, 1)


class TestAnalisis(unittest.TestCase):
    def setUp(self):
        self.data = [
            t("2026-09-01", "pemasukan", "gaji", 5000),
            t("2026-09-02", "pengeluaran", "makanan", 100),
            t("2026-09-03", "pengeluaran", "makanan", 300),
            t("2026-10-01", "pengeluaran", "kos", 600),
        ]

    def test_total_per_kategori_terurut(self):
        self.assertEqual(analisis.total_per_kategori(self.data),
                         {"kos": 600.0, "makanan": 400.0})

    def test_rekap_bulanan(self):
        r = analisis.rekap_bulanan(self.data)
        self.assertEqual(r["2026-09"]["saldo"], 4600.0)
        self.assertEqual(r["2026-10"]["saldo"], -600.0)

    def test_hapus_duplikat(self):
        unik, dibuang = analisis.hapus_duplikat(self.data + [self.data[1]])
        self.assertEqual((len(unik), dibuang), (4, 1))

    def test_cari_dan_filter(self):
        self.assertEqual(len(analisis.cari(self.data, "MAKAN")), 2)
        self.assertEqual(len(analisis.filter_transaksi(self.data, bulan="2026-09")), 3)
        self.assertEqual(analisis.cari(self.data, "  "), [])

    def test_edge_data_kosong(self):
        r = analisis.ringkasan([])
        self.assertEqual(r["saldo"], 0)
        self.assertIsNone(r["kategori_pengeluaran_terbesar"])
        self.assertEqual(analisis.persentase_per_kategori({}), {})

    def test_status_saldo(self):
        self.assertEqual([analisis.status_saldo(x) for x in (1, 0, -1)],
                         ["SURPLUS", "IMPAS", "DEFISIT"])


class TestIO(unittest.TestCase):
    def tulis_sementara(self, isi, akhiran=".csv"):
        f = tempfile.NamedTemporaryFile("w", suffix=akhiran, delete=False, encoding="utf-8")
        f.write(isi)
        f.close()
        self.addCleanup(os.remove, f.name)
        return f.name

    def test_file_tidak_ada(self):
        with self.assertRaises(FileNotFoundError):
            io_utils.baca_transaksi("tidak_ada.csv")

    def test_format_tidak_didukung(self):
        with self.assertRaises(FormatTidakDidukungError):
            io_utils.baca_transaksi(self.tulis_sementara("x", ".txt"))

    def test_file_kosong_dan_header_kurang(self):
        with self.assertRaises(DataTidakValidError):
            io_utils.baca_transaksi(self.tulis_sementara("tanggal,deskripsi,kategori,jumlah,tipe\n"))
        with self.assertRaises(DataTidakValidError):
            io_utils.baca_transaksi(self.tulis_sementara("a,b\n1,2\n"))

    def test_baris_rusak_dilewati(self):
        isi = ("tanggal,deskripsi,kategori,jumlah,tipe\n"
               "2026-09-01,ok,gaji,100,pemasukan\n"
               "2026-09-02,salah,gaji,1.000,pemasukan\n")
        valid, galat = io_utils.baca_transaksi(self.tulis_sementara(isi))
        self.assertEqual((len(valid), len(galat)), (1, 1))
        self.assertIn("Baris 3", galat[0])

    def test_json_rusak(self):
        with self.assertRaises(DataTidakValidError):
            io_utils.baca_transaksi(self.tulis_sementara("[{oops", ".json"))

    def test_jumlah_tidak_valid(self):
        for buruk in ("abc", "-5", "0", "nan", "inf", ""):
            with self.assertRaises(DataTidakValidError, msg=buruk):
                io_utils.parse_jumlah(buruk, 1)


if __name__ == "__main__":
    unittest.main()
