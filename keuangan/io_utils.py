"""Membaca dan menulis file CSV / JSON, serta memvalidasi tiap baris."""

import csv
import json
import math
import re
from datetime import datetime
from pathlib import Path

from .exceptions import DataTidakValidError, FormatTidakDidukungError

KOLOM_WAJIB = ("tanggal", "deskripsi", "kategori", "jumlah", "tipe")
TIPE_VALID = {"pemasukan", "pengeluaran"}
POLA_RIBUAN = re.compile(r"^\d{1,3}(\.\d{3})+$")


# ---------------------------------------------------------------- validasi
def parse_jumlah(teks, nomor):
    """Ubah teks jumlah menjadi float positif (2 desimal).

    Raises:
        DataTidakValidError: kosong, bukan angka, tidak terhingga, atau <= 0.
    """
    teks = str(teks).strip()
    if not teks:
        raise DataTidakValidError(f"Baris {nomor}: jumlah kosong")
    # "1.000" / "1.500.000" lolos float() sebagai 1.0 / 1.5 (salah diam-diam).
    # Pola pemisah ribuan ala Indonesia ditolak agar tidak mencatat angka keliru.
    if POLA_RIBUAN.match(teks):
        raise DataTidakValidError(
            f"Baris {nomor}: jumlah '{teks}' memakai pemisah ribuan "
            "(tulis 1500000 atau 1500000.50)"
        )
    try:
        nilai = float(teks)
    except ValueError:
        raise DataTidakValidError(
            f"Baris {nomor}: jumlah '{teks}' bukan angka "
            "(tulis 1500000 atau 1500000.50, tanpa pemisah ribuan)"
        ) from None
    if not math.isfinite(nilai):
        raise DataTidakValidError(f"Baris {nomor}: jumlah '{teks}' tidak valid")
    if nilai <= 0:
        raise DataTidakValidError(f"Baris {nomor}: jumlah harus lebih dari 0")
    return round(nilai, 2)


def parse_tanggal(teks, nomor):
    """Validasi tanggal berformat YYYY-MM-DD, kembalikan string ISO."""
    try:
        return datetime.strptime(str(teks).strip(), "%Y-%m-%d").date().isoformat()
    except ValueError:
        raise DataTidakValidError(
            f"Baris {nomor}: tanggal '{teks}' tidak valid (format YYYY-MM-DD)"
        ) from None


def normalisasi_baris(baris, nomor):
    """Validasi satu baris mentah (dict) dan kembalikan dict bersih."""
    if not isinstance(baris, dict):
        raise DataTidakValidError(f"Baris {nomor}: bukan objek/baris data")
    kurang = [k for k in KOLOM_WAJIB if k not in baris or baris[k] is None]
    if kurang:
        raise DataTidakValidError(f"Baris {nomor}: kolom hilang {kurang}")

    tipe = str(baris["tipe"]).strip().lower()
    if tipe not in TIPE_VALID:
        raise DataTidakValidError(
            f"Baris {nomor}: tipe '{baris['tipe']}' harus pemasukan/pengeluaran"
        )
    kategori = str(baris["kategori"]).strip().lower()
    if not kategori:
        raise DataTidakValidError(f"Baris {nomor}: kategori kosong")

    tanggal = parse_tanggal(baris["tanggal"], nomor)
    return {
        "tanggal": tanggal,
        "bulan": tanggal[:7],
        "deskripsi": str(baris["deskripsi"]).strip(),
        "kategori": kategori,
        "jumlah": parse_jumlah(baris["jumlah"], nomor),
        "tipe": tipe,
    }


# ----------------------------------------------------------------- membaca
def _baca_csv_mentah(path):
    # utf-8-sig membuang BOM yang sering muncul dari Excel
    with open(path, newline="", encoding="utf-8-sig") as f:
        pembaca = csv.DictReader(f)
        if pembaca.fieldnames is None:
            return []
        kolom = {k.strip().lower() for k in pembaca.fieldnames if k}
        kurang = [k for k in KOLOM_WAJIB if k not in kolom]
        if kurang:
            raise DataTidakValidError(f"Header CSV kurang kolom: {kurang}")
        return [{(k or "").strip().lower(): v for k, v in b.items()} for b in pembaca]


def _baca_json_mentah(path):
    try:
        with open(path, encoding="utf-8-sig") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise DataTidakValidError(
            f"JSON rusak di baris {e.lineno}, kolom {e.colno}: {e.msg}"
        ) from e
    if not isinstance(data, list):
        raise DataTidakValidError("JSON harus berupa daftar (list) transaksi")
    return data


def baca_transaksi(path):
    """Baca file transaksi dan kembalikan (transaksi_valid, daftar_galat).

    Baris yang tidak valid dilewati dan dicatat di daftar_galat, sehingga satu
    baris rusak tidak menggagalkan seluruh proses.

    Raises:
        FileNotFoundError: file tidak ada.
        FormatTidakDidukungError: ekstensi bukan .csv/.json.
        DataTidakValidError: file kosong, header kurang, atau JSON rusak.
    """
    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(f"File tidak ditemukan: {p}")

    ekstensi = p.suffix.lower()
    if ekstensi == ".csv":
        mentah = _baca_csv_mentah(p)
        nomor_awal = 2  # baris 1 adalah header
    elif ekstensi == ".json":
        mentah = _baca_json_mentah(p)
        nomor_awal = 1
    else:
        raise FormatTidakDidukungError(
            f"Format '{ekstensi}' tidak didukung, gunakan .csv atau .json"
        )

    if not mentah:
        raise DataTidakValidError(f"File {p.name} tidak berisi data transaksi")

    valid, galat = [], []
    for nomor, baris in enumerate(mentah, start=nomor_awal):
        try:
            valid.append(normalisasi_baris(baris, nomor))
        except DataTidakValidError as e:
            galat.append(str(e))
    return valid, galat


# ---------------------------------------------------------------- menulis
def tulis_csv(path, baris, kolom):
    """Tulis list of dict ke CSV dengan urutan kolom tertentu."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", newline="", encoding="utf-8") as f:
        penulis = csv.DictWriter(f, fieldnames=kolom, extrasaction="ignore")
        penulis.writeheader()
        penulis.writerows(baris)


def tulis_json(path, data):
    """Tulis data apa pun yang bisa di-serialize ke file JSON."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
