"""Antarmuka command line: parsing argumen, alur program, penanganan error."""

import argparse
import logging
import sys

from . import analisis, io_utils, laporan
from .exceptions import KeuanganError

log = logging.getLogger("keuangan")


def buat_parser():
    """Bangun parser argumen beserta subperintah."""
    induk = argparse.ArgumentParser(
        prog="main.py", description="Pengolah transaksi keuangan pribadi (CSV/JSON)."
    )
    induk.add_argument("--debug", action="store_true",
                       help="tampilkan log detail dan traceback lengkap")
    sub = induk.add_subparsers(dest="perintah", required=True)

    def tambah(nama, bantuan):
        p = sub.add_parser(nama, help=bantuan)
        p.add_argument("-i", "--input", required=True, help="file .csv atau .json")
        return p

    p = tambah("rekap", "tampilkan rekap; opsional simpan ke file")
    p.add_argument("-o", "--output", help="simpan rekap (.json = lengkap, .csv = per bulan)")

    p = tambah("cari", "cari berdasarkan kata kunci")
    p.add_argument("kata_kunci")

    p = tambah("filter", "saring transaksi")
    p.add_argument("--tipe", choices=sorted(io_utils.TIPE_VALID))
    p.add_argument("--kategori")
    p.add_argument("--bulan", help="format YYYY-MM")
    p.add_argument("--min", type=float, dest="jumlah_min", help="jumlah minimum")

    p = tambah("bersihkan", "hapus duplikat dan simpan hasilnya")
    p.add_argument("-o", "--output", required=True, help="file keluaran .csv/.json")

    tambah("kategori", "daftar kategori unik")
    tambah("menu", "mode interaktif (menu berulang)")
    return induk


def muat_data(path):
    """Baca file, lalu tampilkan peringatan untuk baris yang dilewati."""
    transaksi, galat = io_utils.baca_transaksi(path)
    for pesan in galat:
        print(f"[PERINGATAN] {pesan} -> dilewati", file=sys.stderr)
    if not transaksi:
        raise KeuanganError("Tidak ada baris valid yang bisa diproses")
    log.debug("dimuat %d valid, %d dilewati", len(transaksi), len(galat))
    return transaksi


def simpan(path, transaksi_atau_data, kolom=None):
    """Simpan ke .json atau .csv sesuai ekstensi path."""
    if str(path).lower().endswith(".json"):
        io_utils.tulis_json(path, transaksi_atau_data)
    else:
        io_utils.tulis_csv(path, transaksi_atau_data, kolom)
    print(f"Tersimpan: {path}")


# ----------------------------------------------------------- perintah
def jalankan_rekap(args):
    transaksi = muat_data(args.input)
    print(laporan.teks_rekap(transaksi))
    if args.output:
        if args.output.lower().endswith(".json"):
            simpan(args.output, laporan.data_rekap(transaksi))
        else:
            simpan(args.output, laporan.baris_rekap_bulanan(transaksi),
                   ["bulan", "pemasukan", "pengeluaran", "saldo"])


def jalankan_cari(args):
    hasil = analisis.cari(muat_data(args.input), args.kata_kunci)
    print(laporan.tabel_transaksi(hasil))


def jalankan_filter(args):
    hasil = analisis.filter_transaksi(
        muat_data(args.input), args.tipe, args.kategori, args.bulan, args.jumlah_min
    )
    print(laporan.tabel_transaksi(hasil))


def jalankan_bersihkan(args):
    unik, dibuang = analisis.hapus_duplikat(muat_data(args.input))
    print(f"{dibuang} duplikat dibuang, {len(unik)} transaksi tersisa.")
    simpan(args.output, unik, list(io_utils.KOLOM_WAJIB))


def jalankan_kategori(args):
    for k in analisis.daftar_kategori(muat_data(args.input)):
        print(f"- {k}")


def jalankan_menu(args):
    """Menu interaktif; perulangan while berjalan sampai pengguna memilih keluar."""
    transaksi = muat_data(args.input)
    while True:
        print("\n1) Rekap  2) Cari  3) Daftar kategori  0) Keluar")
        try:
            pilihan = input("Pilih: ").strip()
        except EOFError:  # input ditutup (mis. di-pipe) -> keluar dengan rapi
            break
        if pilihan == "1":
            print(laporan.teks_rekap(transaksi))
        elif pilihan == "2":
            kata = input("Kata kunci: ")
            print(laporan.tabel_transaksi(analisis.cari(transaksi, kata)))
        elif pilihan == "3":
            print(", ".join(analisis.daftar_kategori(transaksi)))
        elif pilihan == "0":
            break
        else:
            print("Pilihan tidak dikenal, coba lagi.")


PERINTAH = {
    "rekap": jalankan_rekap,
    "cari": jalankan_cari,
    "filter": jalankan_filter,
    "bersihkan": jalankan_bersihkan,
    "kategori": jalankan_kategori,
    "menu": jalankan_menu,
}


def main(argv=None):
    """Titik masuk. Mengembalikan kode keluar (0 sukses, 1 gagal)."""
    args = buat_parser().parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.debug else logging.WARNING,
        format="%(levelname)s %(name)s: %(message)s",
    )
    try:
        PERINTAH[args.perintah](args)
    except (KeuanganError, FileNotFoundError) as e:
        if args.debug:
            raise  # tampilkan traceback penuh untuk debugging
        print(f"[ERROR] {e}", file=sys.stderr)
        return 1
    return 0
